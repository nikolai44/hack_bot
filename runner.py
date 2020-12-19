import argparse
from subprocess import Popen, PIPE
from model.game import Game

server_ip = "wss://gameapi.it-god.ru"
user_id = "0dfdc192-673e-46b7-ab56-865e94984ed0"
bot_id = "8480093f-0c58-4c14-ac8a-ee2984a74701"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runner for ITGod')

    parser.add_argument('-i', '--ip', type=str, nargs='?', help='Server IP', default=server_ip)
    parser.add_argument('-b', '--bot', type=str, nargs='?', help='Bot Id', default=bot_id)
    parser.add_argument('-u', '--user', type=str, nargs='?', help='User Id', default=user_id)
    parser.add_argument('-g', '--game', type=str, nargs='?', help='Game Id')
    parser.add_argument('-s', '--srv', action='store_true', help='Service argument')

    args = parser.parse_args()

    process = Popen(["python", "-u", "bot.py"], stdout=PIPE, stdin=PIPE)

    if args.srv:
        Game(process, "{}/game".format(args.ip), None, args.bot, args.game)
    else:
        Game(process, "{}/game".format(args.ip), args.user, args.bot, None)
