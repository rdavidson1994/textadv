from agent import WorldEvents, Town
import schedule
import wide
import namemaker
import sites
import direction
from world import make_player

day = 1000*60*60*24

if __name__ == "__main__":
    world_schedule = schedule.Schedule()
    world_map = wide.Overworld(
        sched=world_schedule,
        width=50,
        height=50,
    )

    world_events = WorldEvents(world_map)

    town_n = 10
    cave_n = 24
    caves = [
        sites.RuneCave.at_point(
            location=world_map,
            coordinates=world_map.random_point(),
            direction=direction.down,
            landmark_name=namemaker.make_name()+"cave"
        )
        for i in range(cave_n)
    ]

    towns = [
        Town(
            name=namemaker.make_name(),
            location=world_map,
            coordinates=world_map.random_point(),
        )
        for i in range(town_n)
    ]
    world_schedule.run_game(250*day)

    dude = make_player(
        location=world_map,
        coordinates=world_map.random_point(),
        landmarks=set(town.site.landmark for town in towns),
        use_web_output=False,
    )
    # dude.view_location()
    world_schedule.run_game()
