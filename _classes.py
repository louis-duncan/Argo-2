from _globals import *
import random
import time


class Game:
    def __init__(self):
        self.entities = []

    def get_entities(self, pos):
        results = []
        for e in self.entities:
            if e.pos[0] == pos[0] and e.pos[1] == pos[1]:
                results.append(e)
        return results


class Entity:
    def __init__(self,
                 parent,
                 entity_id=ANY_ID,
                 name="no_name",
                 colour=BLACK,
                 pos=(0, 0),
                 facing=NORTH,
                 created_by=None,
                 ttl=None):
        self.parent = parent
        self.entity_id = entity_id
        self.name = name
        self.colour = colour
        self.pos = pos
        self.facing = facing
        self.created_time = time.time()
        self.created_by = created_by
        self.ttl = ttl

        if self.entity_id is None:
            self.entity_id = random.randint(10000, 99999)

    def destroy(self):
        self.parent.entities.remove(self)

    def move(self, direction=FORWARD):
        assert direction in (FORWARD, BACKWARD)

        if self.facing in (NORTH, NORTH_WEST, NORTH_EAST):
            self.pos[0] -= direction
        elif self.facing in (SOUTH, SOUTH_WEST, SOUTH_EAST):
            self.pos[0] += direction

        if self.facing in (WEST, NORTH_WEST, SOUTH_WEST):
            self.pos[1] -= direction
        elif self.facing in (EAST, NORTH_EAST, SOUTH_EAST):
            self.pos[1] += direction

    def turn(self, direction):
        assert direction in (LEFT, RIGHT)
        self.facing = DIRECTIONS[(DIRECTIONS.index(self.facing) + direction) % len(DIRECTIONS)]

    def tick(self):
        if (self.ttl is not None) and (self.created_time + self.ttl >= time.time()):
            self.destroy()


class Ship(Entity):
    def __init__(self,
                 parent,
                 entity_id=ANY_ID,
                 name="no_name",
                 colour=BLACK,
                 pos=(0, 0),
                 facing=NORTH,
                 created_by=None,
                 ttl=None):
        super().__init__(parent,
                         entity_id,
                         name,
                         colour,
                         pos,
                         facing,
                         created_by,
                         ttl)

        self.trail_ttl = 60

        self.reactor_overload = False
        self.shields_level = 0
        self.hull_hp = 24

        self.systems = [
            ShipSystem(self, "Reactor_Output"),
            ShipSystem(self, "Shields"),
            ShipSystem(self, "Weapons"),
            ShipSystem(self, "Life_Support"),
            ShipSystem(self, "Holograms")
        ]

    def _spawn_trail(self, pos=None):
        if pos is None:
            pos = self.pos
        self.parent.entities.append(
            Trail(
                parent=self.parent,
                colour=self.colour,
                pos=pos,
                facing=self.facing,
                created_by=self,
                ttl=self.trail_ttl
            )
        )

    def _spawn_debris(self, pos=None):
        if pos is None:
            pos = self.pos
        self.parent.entities.append(
            Debris(
                parent=self.parent,
                colour=self.colour,
                pos=pos,
                created_by=self
            )
        )

    def move(self, direction=FORWARD):
        self._spawn_trail()
        super().move(direction)

    def get_states(self):
        return {s.name: s.level() for s in self.systems}

    def destroy(self):
        self._spawn_debris()
        super().destroy()


class ShipSystem:
    def __init__(self, parent, name, level=0, max_level=8):
        self.parent = parent
        self.name = name
        self._level = level
        self.max_level = max_level
        self.modifiers = []

    def level(self, lvl=None):
        if lvl is not None:
            self._level = lvl
            return
        result = self._level
        m = 0
        while m < len(self.modifiers):
            if self.modifiers[m].expiry < time.time():
                self.modifiers.remove(self.modifiers[m])
            else:
                result += self.modifiers[m].amount
                m += 1
        return result


class SystemModifier:
    def __init__(self, amount, ttl):
        self.amount = amount
        self.expiry = time.time() + ttl


class Trail(Entity):
    def __init__(self,
                 parent,
                 entity_id=ANY_ID,
                 name="trail",
                 colour=BLACK,
                 pos=(0, 0),
                 facing=NORTH,
                 created_by=None,
                 ttl=60):
        super().__init__(parent,
                         entity_id,
                         name,
                         colour,
                         pos,
                         facing,
                         created_by,
                         ttl)


class Debris(Entity):
    def __init__(self,
                 parent,
                 entity_id=ANY_ID,
                 name="no_name",
                 colour=BLACK,
                 pos=(0, 0),
                 facing=NORTH,
                 created_by=None,
                 ttl=None):
        super().__init__(parent,
                         entity_id=entity_id,
                         name=name,
                         colour=colour,
                         pos=pos,
                         facing=facing,
                         created_by=created_by,
                         ttl=ttl)
        self._last_turn_time = 0
        self._turn_interval = 2

    def tick(self):
        if self._last_turn_time + self._turn_interval < time.time():
            self.turn(RIGHT)
            self._last_turn_time = time.time()
        super().tick()


class Station(Entity):
    def __init__(self,
                 parent,
                 entity_id=ANY_ID,
                 name="no_name",
                 colour=BLACK,
                 pos=(0, 0),
                 facing=NORTH,
                 created_by=None,
                 ttl=None):
        super().__init__(parent,
                         entity_id,
                         name,
                         colour,
                         pos,
                         facing,
                         created_by,
                         ttl)
        self._last_turn_time = 0
        self._turn_interval = 3

    def tick(self):
        if self._last_turn_time + self._turn_interval < time.time():
            self.turn(RIGHT)
            self._last_turn_time = time.time()
        super().tick()
