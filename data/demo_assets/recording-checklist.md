# TrafficTwin AI — 60-Second Recording Checklist

## Pre-Recording Setup
- [ ] **Display Layout:** Position terminal window on the left half of the screen and leave the right half open for the SUMO GUI window.
- [ ] **Recording Region:** Record either Full Screen (1080p) or a side-by-side split showing both terminal and SUMO GUI.
- [ ] **Working Directory:** Open terminal in `d:\X\Aarambh-WCE\Project\SUMO-Traffic-Simulator-Tutorial-Prototype`.
- [ ] **Test Run:** Launch `python Traci4.py` once to ensure window placement and close it.

---

## The 60-Second Recording Sequence

| Timestamp | Visual Action / Event | Narration Cue |
| :--- | :--- | :--- |
| **00:00 – 00:10** | Run `python Traci4.py` in the terminal.<br>SUMO GUI window appears on the right.<br>Intersection `J6` is visible with passenger traffic flowing smoothly East-West and North-South. | *"Welcome to TrafficTwin AI. Here you see our real-time simulation foundation running Eclipse SUMO coupled directly with our Python TraCI controller."* |
| **00:10 – 00:25** | Point cursor at the terminal and SUMO GUI.<br>Show terminal log: TraCI establishes socket connection and begins advancing steps at 100ms delay. | *"Through TraCI, our controller streams live road telematics, vehicle positions, and intersection signal states at 20 ticks per second."* |
| **00:25 – 00:45** | At ~step 200 (simulation second 10), red vehicle `emerg_1` enters edge `E5`.<br>Terminal outputs:<br>`Vehicle emerg_1 is on edge e5`<br>`TLS J6, Current phase: 0, Desired phase: 2`<br>`Extended phase / Shortened phase...`<br>In SUMO GUI, intersection `J6` turns green for `E5`. | *"Notice an emergency vehicle approaching on edge E5. Our controller immediately detects it via TraCI, preempts the cross-traffic schedule, and switches junction J6 to green, creating an uninterrupted green wave corridor."* |
| **00:45 – 00:55** | `emerg_1` crosses through junction `J6` without stopping.<br>Terminal logs: `Resetting traffic light J6 to normal operation.`<br>Signal J6 returns to standard cyclic phase. | *"Once the vehicle safely clears the intersection, TrafficTwin automatically restores standard signal operations, preventing secondary gridlock."* |
| **00:55 – 01:05** | Switch focus back to slide or summarize.<br>Close SUMO GUI or press Ctrl+C in terminal. | *"This closed-loop control pipeline is the foundational execution layer for our upcoming AI and Reinforcement Learning traffic optimization model."* |

---

## Safe Visual Actions in SUMO GUI During Recording
1. **Zoom in slightly** on intersection `J6` using mouse scroll wheel so the vehicle shapes and traffic lights are crisp.
2. In the top bar, you can set the view schema to **"real world"** if desired, or keep default **"standard"**.
3. **Do not** pause or drag the simulation slider in SUMO GUI manually — TraCI is controlling step progression automatically.
