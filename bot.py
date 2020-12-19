from model.hero import *
from model.abilites import Ability, AbilityType
from model.map import Map
from model.parameters import Parameters
from model.state import State
from model.abilites import AbilityType
from model.teams import Teams
from model.buildings import Building
from model.squads import Squad
import json
import random
from typing import List
import sys
import time

game = json.loads(input())
game_map = Map(game)  # карта игрового мира
game_params = Parameters(game)  # параметры игры
game_teams = Teams(game)  # моя команда

count = 0

class BaseGame:
    def tower_upgrade(self, my_buildings):
        # Upgrade башни
        if my_buildings[0].level.id < len(game_params.tower_levels) - 1:
            # Если хватает стоимости на upgrade
            update_coast = game_params.get_tower_level(my_buildings[0].level.id + 1).update_coast
            if update_coast < my_buildings[0].creeps_count:
                print(game_teams.my_her.upgrade_tower(my_buildings[0].id))
                print("в начальном здании делаем апгрейд", file=sys.stderr)
                my_buildings[0].creeps_count -= update_coast


class MagGame(BaseGame):
    pos = "Стартовая позиция"
    tick = 1
    def __init__(self):
        pass

    def build_exchange(self):
        # если враг применил абилку обмен башнями
        build_exchange = self.state.enemy_active_abilities(AbilityType.Build_exchange)
        if len(build_exchange) > 0:
            print("противник свапнул башни, отсвапываем", file=sys.stderr)
            print(game_teams.my_her.exchange(self.enemy_buildings[0].id, self.my_buildings[0].id))
        else:
            min_my = min(self.my_buildings, key=lambda x: x.creeps_count)
            max_enemy = max(self.enemy_buildings, key=lambda x: x.creeps_count)
            if max_enemy.creeps_count - min_my.creeps_count > 10:
                print("разница > 10 юнитов, свапаем башни", file=sys.stderr)
                print(game_teams.my_her.exchange(max_enemy.id, min_my.id))

    def chuma(self):
        # для эффективности применяем ближе к башне
        if len(self.my_squads) > 1:
            # сколько тиков первому отряду осталось до башни
            left_to_aim = self.my_squads[0].way.left / self.my_squads[0].speed
            # если первый отряд находится в зоне инициализации абилки
            plague_parameters = game_params.get_ability_parameters(AbilityType.Plague)
            if plague_parameters.cast_time + 30 > left_to_aim:
                print("Применяем чуму к начальному зданию врага", file=sys.stderr)
                print(game_teams.my_her.plague(self.enemy_buildings[0].id))
        print("Применяем чуму к начальному зданию врага", file=sys.stderr)
        print(game_teams.my_her.plague(self.enemy_buildings[0].id))

    def strategy_abyls(self):
        if self.enemy_buildings:
            # проверяем доступность абилки Чума
            if self.state.ability_ready(AbilityType.Plague):
                print("доступна чума", file=sys.stderr)
                self.chuma()

            # проверяем доступность абилки Обмен башнями
            print()
            if self.state.ability_ready(AbilityType.Build_exchange):
                print("доступен свап башен", file=sys.stderr)
                self.build_exchange()

    def speed_send(self, from_towers: List[Building], to: Building, size: int=1000):
        for tower in from_towers:
            if tower.id not in self.attacked:
                if tower.creeps_count <= size:
                    print("отправляем всех из башни", file=sys.stderr)
                    print(game_teams.my_her.move(tower.id, to.id, 1))
                    tower.creeps_count = 0
                else:
                    print(f"отправляем {size}({int(size / tower.creeps_count * 100)}%) солдат из башни {tower.id}", file=sys.stderr)
                    print(game_teams.my_her.move(tower.id, to.id, size / tower.creeps_count))
                    tower.creeps_count -= size

    def strategy_moves(self):
        print(self.pos, file=sys.stderr)
        print("Tick: ", self.tick, file=sys.stderr)
        if self.pos == "Стартовая позиция":
            self.start_pos = self.my_buildings[0]
            self.pos = "Занимаем стартовые башни"
            self.goto = game_map.get_nearest_towers(self.my_buildings[0].id, self.neutral_buildings)[:2]
            print("Соседних башен ", len(self.goto), file=sys.stderr)
        if self.pos == "Занимаем стартовые башни":
            # if self.my_buildings[0] < 22:
            #     return
            if self.tick == 25:
                print(f"Ускоряемся, координаты {game_map.get_tower_location(self.start_pos.id)}", file=sys.stderr)
                print(self.start_pos.id, file=sys.stderr)
                print(game_teams.my_her.speed_up(game_map.get_tower_location(self.start_pos.id)))
                return
            if self.tick == 1:
                print(f"Захватываем башни {','.join(str(f.id) for f in self.goto)}", file=sys.stderr)
                half = self.start_pos.creeps_count / 2
                for near in self.goto:
                    self.speed_send([self.start_pos], near, half)
                return
            if self.tick < 40:
                return
            self.pos = "Захват территорий"
        if self.pos == "Захват территорий":
            # считаем сколько есть воинов в башнях
            army_in_towers_count = 0
            for my_building in self.my_buildings:
                if my_building.id not in self.attacked:
                    army_in_towers_count += my_building.creeps_count
            print(f"В башнях {army_in_towers_count} солдат", file=sys.stderr)

            i = 0
            if self.neutral_buildings and self.enemy_buildings:
                nearest = game_map.get_nearest_towers(self.start_pos.id,
                                                      self.neutral_buildings + self.enemy_buildings)
            elif self.neutral_buildings:
                nearest = game_map.get_nearest_towers(self.start_pos.id, self.neutral_buildings)
            else:
                nearest = game_map.get_nearest_towers(self.start_pos.id, self.enemy_buildings)

            while (army_in_towers_count > 12):
                # занимаем башни
                self.speed_send(self.my_buildings, nearest[i], 12)
                army_in_towers_count -= 12
                i += 1
        else:
            return

    def loop(self):
        while True:
            try:
                self.state = State(input(), game_teams, game_params)
                self.my_buildings = self.state.my_buildings()
                self.my_squads: List[Squad] = self.state.my_squads()
                self.enemy_buildings = self.state.enemy_buildings()
                self.enemy_squads: List[Squad] = self.state.enemy_squads()
                self.neutral_buildings = self.state.neutral_buildings()
                self.forges_buildings = self.state.forges_buildings()

                self.strategy_abyls()

                if self.my_squads:
                    for squad in self.my_squads:
                        print(f"В скваде из {squad.from_id} в {squad.to_id} {squad.creeps_count} солдат", file=sys.stderr)
                else:
                    print("Никто из солдат не перемещается", file=sys.stderr)

                enemy_abyls: List[Ability] = self.state.enemy_active_abilities()
                if enemy_abyls:
                    for ability in enemy_abyls:
                        print(f"Враг наслал {ability.ability}", file=sys.stderr)

                self.attacked = []
                for squad in self.enemy_squads:
                    print(f"Врагу идти ", squad.way.left, file=sys.stderr)
                    if squad.to_id in self.my_buildings and squad.way.left < 2.0 \
                        and squad.creeps_count > 3:
                        self.attacked.append(squad.to_id)
                self.strategy_moves()

                self.tick += 1
                print("Задержка чтобы не забанили 0.3 сек", file=sys.stderr)
                time.sleep(0.3)
            except Exception as e:
                 raise Exception(e)
            finally:
                """  Требуется для получения нового состояния игры  """
                print("end")
            # except Exception as e:
            #     print(str(e), file=sys.stderr)
            # finally:
            #     """  Требуется для получения нового состояния игры  """
            #     print("end")


game_event_loop = MagGame()
game_event_loop.loop()
