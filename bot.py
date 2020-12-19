from model.hero import *
from model.map import Map
from model.parameters import Parameters
from model.state import State
from model.abilites import AbilityType
from model.teams import Teams
from model.buildings import Building
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
    def __init__(self):
        pass

    def build_exchange(self):
        # если враг применил абилку обмен башнями
        build_exchange = self.state.enemy_active_abilities(AbilityType.Build_exchange)
        if len(build_exchange) > 0:
            print("противник свапнул башни, отсвапываем", file=sys.stderr)
            print(game_teams.my_her.exchange(self.enemy_buildings[0].id, self.my_buildings[0].id))
        else:
            if self.my_buildings[0].creeps_count < 10:
                print("в начальном здании < 10 юнитов, свапаем с начальной противника", file=sys.stderr)
                print(game_teams.my_her.exchange(self.enemy_buildings[0].id, self.my_buildings[0].id))

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

    def strategy_abyls(self):
        # проверяем доступность абилки Обмен башнями
        print()
        if self.state.ability_ready(AbilityType.Build_exchange):
            print("доступен свап башен", file=sys.stderr)
            self.build_exchange()
        # проверяем доступность абилки Чума
        if self.state.ability_ready(AbilityType.Plague):
            print("доступна чума", file=sys.stderr)
            self.chuma()

    def speed_send(self, from_towers: List[Building], to: Building):
        global count
        for tower in from_towers:
            print(game_teams.my_her.move(tower.id, to.id, 1))
            self.count_steps += 1

    def strategy_moves(self):
        # занимаем башни
        for my_building in self.my_buildings:
            print("Отправляем всех на захват ближайшей башни", file=sys.stderr)
            nearest = game_map.get_nearest_towers(self.my_buildings[0].id, self.neutral_buildings)
            self.speed_send(self.my_buildings, nearest[0])
            print("Задержка чтобы не забанили 0.3 сек", file=sys.stderr)
            time.sleep(0.3)

    def loop(self):
        while True:
            try:
                self.state = State(input(), game_teams, game_params)
                self.my_buildings = self.state.my_buildings()
                self.my_squads = self.state.my_squads().sort(key=lambda c: c.way.left, reverse=False)
                self.enemy_buildings = self.state.enemy_buildings()
                self.enemy_squads = self.state.enemy_squads()
                self.neutral_buildings = self.state.neutral_buildings()
                self.forges_buildings = self.state.forges_buildings()

                self.count_steps = 0

                print("Все способности отключены", file=sys.stderr)
                # self.strategy_abyls()
                self.strategy_moves()
            except Exception as e:
                print(str(e), file=sys.stderr)
            finally:
                """  Требуется для получения нового состояния игры  """
                print("end")


game_event_loop = MagGame()
game_event_loop.loop()
