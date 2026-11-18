// Solves one flop (BB checks to the preflop raiser) and writes the
// strategies at the decision points the trainer drills, as JSON.
use postflop_solver::*;
use serde_json::{json, Map, Value};
use std::time::Instant;

fn r3(x: f32) -> f64 {
    (x as f64 * 1000.0).round() / 1000.0
}

fn act_name(a: &Action, pot: i32) -> String {
    match a {
        Action::Fold => "Fold".into(),
        Action::Check => "Check".into(),
        Action::Call => "Call".into(),
        Action::Bet(x) => format!("Bet {}%", ((*x as f64) / pot as f64 * 100.0).round()),
        Action::Raise(_) => "Raise".into(),
        Action::AllIn(_) => "All-in".into(),
        _ => format!("{:?}", a),
    }
}

/// The current node: actions, and per combo [weight, equity, freq per action].
fn snap(game: &mut PostFlopGame, pot_now: i32) -> Value {
    game.cache_normalized_weights();
    let p = game.current_player();
    let actions: Vec<String> = game.available_actions().iter().map(|a| act_name(a, pot_now)).collect();
    let cards = game.private_cards(p).to_vec();
    let names = holes_to_strings(&cards).unwrap();
    let strat = game.strategy();
    let w = game.normalized_weights(p).to_vec();
    let eq = game.equity(p);
    let n = cards.len();
    let mut hands = Map::new();
    let mut agg = vec![0f64; actions.len()];
    let (mut tot, mut eq_sum) = (0f64, 0f64);
    for i in 0..n {
        if w[i] <= 1e-6 {
            continue;
        }
        let mut v = vec![json!(r3(w[i])), json!(r3(eq[i]))];
        for a in 0..actions.len() {
            let f = strat[i + a * n];
            v.push(json!(r3(f)));
            agg[a] += (f * w[i]) as f64;
        }
        tot += w[i] as f64;
        eq_sum += (eq[i] * w[i]) as f64;
        hands.insert(names[i].clone(), Value::Array(v));
    }
    let agg: Vec<f64> = agg.iter().map(|x| (x / tot * 1000.0).round() / 1000.0).collect();
    json!({
        "player": if p == 0 { "OOP" } else { "IP" },
        "pot_bb": pot_now as f64 / 10.0,
        "actions": actions,
        "agg": agg,
        "range_equity": (eq_sum / tot * 1000.0).round() / 1000.0,
        "hands": hands
    })
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let (oop_r, ip_r, flop, turns, out) = (&a[1], &a[2], &a[3], &a[4], &a[5]);
    let target: f32 = a[6].parse().unwrap(); // exploitability target, fraction of pot
    let iters: u32 = a[7].parse().unwrap();

    let card_config = CardConfig {
        range: [oop_r.parse().unwrap(), ip_r.parse().unwrap()],
        flop: flop_from_str(flop).unwrap(),
        turn: NOT_DEALT,
        river: NOT_DEALT,
    };
    // Units are 0.1bb: 5.5bb pot, 97.5bb behind.
    let tree_config = TreeConfig {
        initial_state: BoardState::Flop,
        starting_pot: 55,
        effective_stack: 975,
        rake_rate: 0.0,
        rake_cap: 0.0,
        flop_bet_sizes: [
            BetSizeOptions::try_from(("", "3x")).unwrap(),        // BB: check, check-raise 3x
            BetSizeOptions::try_from(("33%, 75%", "")).unwrap(),  // BTN: c-bet small or big
        ],
        turn_bet_sizes: [
            BetSizeOptions::try_from(("66%", "")).unwrap(),
            BetSizeOptions::try_from(("66%", "")).unwrap(),
        ],
        river_bet_sizes: [
            BetSizeOptions::try_from(("75%", "")).unwrap(),
            BetSizeOptions::try_from(("75%", "")).unwrap(),
        ],
        turn_donk_sizes: None,
        river_donk_sizes: None,
        add_allin_threshold: 0.0,
        force_allin_threshold: 0.15,
        merging_threshold: 0.1,
    };
    let tree = ActionTree::new(tree_config).unwrap();
    let mut game = PostFlopGame::with_config(card_config, tree).unwrap();
    let (m, mc) = game.memory_usage();
    let compress = m > 3_000_000_000;
    eprintln!("{flop}: memory {:.2}GB raw / {:.2}GB compressed, compress={compress}", m as f64 / 1e9, mc as f64 / 1e9);
    game.allocate_memory(compress);
    let t = Instant::now();
    let expl = solve(&mut game, iters, 55.0 * target, false);
    let expl_pct = expl / 55.0 * 100.0;
    eprintln!("{flop}: exploitability {:.2}% of pot in {:.0}s", expl_pct, t.elapsed().as_secs_f32());

    let mut nodes = Map::new();
    game.back_to_root();
    game.play(0); // BB checks
    nodes.insert("ip_vs_check".into(), snap(&mut game, 55));
    let ip_actions = game.available_actions();
    for (i, act) in ip_actions.iter().enumerate() {
        if let Action::Bet(x) = act {
            game.back_to_root();
            game.play(0);
            game.play(i);
            let key = format!("oop_vs_bet{}", ((*x as f64) / 55.0 * 100.0).round());
            nodes.insert(key, snap(&mut game, 55 + x));
        }
    }

    // Turn spots: flop goes check, BTN bets 33%, BB calls, then a turn card.
    let mut turn_nodes = Vec::new();
    for tc in turns.split(',').filter(|s| !s.is_empty()) {
        let c = card_from_str(tc).unwrap();
        game.back_to_root();
        game.play(0);
        let acts = game.available_actions();
        let bi = acts.iter().position(|x| matches!(x, Action::Bet(_))).unwrap();
        let bet = if let Action::Bet(x) = acts[bi] { x } else { 0 };
        game.play(bi);
        let ci = game.available_actions().iter().position(|x| matches!(x, Action::Call)).unwrap();
        game.play(ci);
        if game.possible_cards() & (1u64 << c) == 0 {
            continue;
        }
        game.play(c as usize);
        let pot = 55 + 2 * bet;
        let oop_first = snap(&mut game, pot);
        game.play(0); // BB checks the turn
        let ip = snap(&mut game, pot);
        let ip_acts = game.available_actions();
        let mut facing = Value::Null;
        if let Some(bj) = ip_acts.iter().position(|x| matches!(x, Action::Bet(_))) {
            let tb = if let Action::Bet(x) = ip_acts[bj] { x } else { 0 };
            game.play(bj);
            facing = snap(&mut game, pot + tb);
        }
        turn_nodes.push(json!({"card": tc, "oop_first": oop_first, "ip_vs_check": ip, "oop_vs_bet": facing}));
    }
    let outj = json!({
        "flop": flop,
        "exploitability_pct_pot": (expl_pct as f64 * 100.0).round() / 100.0,
        "nodes": nodes,
        "turns": turn_nodes
    });
    std::fs::write(out, serde_json::to_string(&outj).unwrap()).unwrap();
}
