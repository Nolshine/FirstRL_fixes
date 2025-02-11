from __future__ import annotations


import random
from game_map import GameMap
from typing import Iterator, List, Tuple, TYPE_CHECKING
import tile_types
import tcod
import entity_factories

if TYPE_CHECKING:
    from engine import Engine


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y
        
    @property
    def inner(self) -> Tuple[slice, slice]:
        #returns the inside of the room as a 2d array
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)
    
    def intersects(self, other: RectangularRoom) -> bool:
        #Return True if this room overlaps with another RectangulaRoom
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )
    
def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    #Return an L-shaped tunnel between these two points
    x1, y1 = start
    x2, y2 = end

    if random.random() < 0.5: #50% chance for this to happen
        #Move horizontally, then vertically
        corner_x, corner_y = x2, y1
    else:
        #Move vertically, then horizontally
        corner_x, corner_y = x1, y2

    #Generate the coordinates for this tunnel
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y

def place_entities(
    room: RectangularRoom, dungeon: GameMap, maximum_monsters: int, maximum_items: int
) -> None:
    number_of_monsters = random.randint(0, maximum_monsters)
    number_of_items = random.randint(0, maximum_items)
    for i in range(number_of_monsters):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if random.random() < 0.8:
                entity_factories.orc.spawn(dungeon, x, y)
            else:
                entity_factories.troll.spawn(dungeon, x, y)

    for i in range(number_of_items):
        x = random.randint(room.x1 + 1, room.x2 -1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity_factories.health_potion.spawn(dungeon, x, y)


def generate_dungeon(
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        engine: Engine,
        max_monsters_per_room: int,
        max_items_per_room: int,
) -> GameMap:
    #Generate a new dungeon map
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1) #random x cord for the room
        y = random.randint(0, dungeon.height - room_height - 1) #random y cord for the room

        #RectangularRoom class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        #Run through previously made rooms and see if they intersect with this one
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue #This room intersects we try to make another room elsewhere
        #If there are no intersections then the room is okay

        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            #This is the first room, where the player starts, so its centered around the player
            player.place(*new_room.center, dungeon)
        else:
            #Dig out a tunnel between this room and the previous one generated
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor
        
        place_entities(new_room, dungeon, max_monsters_per_room, max_items_per_room)

        #adds new room to the list created
        rooms.append(new_room)
    return dungeon

