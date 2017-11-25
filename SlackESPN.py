from slackclient import SlackClient
from espnff import League
import argparse, os, time




def handle_command(ARGS, CLIENT, command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    message = '''Commands I know:
    list teams
    scores <optional week number>
    does Brandon suck
    '''
    message = ""
    attachments = ""
    if command == "list teams":
        message = '\n'.join(map(lambda x: x.team_name, ARGS.league.teams))
    elif command == "does brandon suck":
        message = 'yes'
    elif 'scores' in command:
        pieces = command.split(' ')
        if len(pieces) == 1:
            message = 'Current Scoreboard'
            matchups = ARGS.league.scoreboard(projections=True)
        else:
            message = 'Scoreboard for week ' + pieces[1]
            matchups = ARGS.league.scoreboard(pieces[1], projections=True)

        attachments = [{
            'fallback': 'A textual representation of your table data',
            'fields': [
                {
                    'title': 'Home',
                    'value': '\n'.join(map(lambda x: x.home_team.team_abbrev + "  " + str(x.home_score) + " (" + str(x.home_projection) + ")", matchups)),
                    'short': True
                },
                {
                    'title': 'Away',
                    'value': '\n'.join(map(lambda x: x.away_team.team_abbrev + "  " + str(x.away_score) + " (" + str(x.away_projection) + ")", matchups)),
                    'short': True
                }
            ]
        }]
    CLIENT.api_call("chat.postMessage", channel=channel, text=message, attachments=attachments, as_user=True)

    # CLIENT.api_call("chat.postMessage", channel=channel, text=message, as_user=True)


def parse_slack_output(ARGS, slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and ARGS.atbot in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(ARGS.atbot)[1].strip().lower(), \
                       output['channel']
    return None, None


def startloop(ARGS, client):
    if client.rtm_connect():
        print(ARGS.botname + " connected and running!")
        while True:
            command, channel = parse_slack_output(ARGS, client.rtm_read())

            if command and channel:
                handle_command(ARGS, CLIENT, command.strip(), channel)
            time.sleep(ARGS.websocketdelay)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")



"""

"""
def getfootballbot(ARGS, client):
    api_call = client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == ARGS.botname:
                print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
                return user.get('id')
    else:
        raise Exception("could not find bot user with the name " + ARGS.botname)

if __name__ == '__main__':
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-slacktoken', default='SLACK_FOOTBALL_TOKEN')
    PARSER.add_argument('-espnleague', default='ESPN_LEAGUE')
    PARSER.add_argument('-botname', default='footballbot')
    PARSER.add_argument('-espns2', default='ESPNS2')
    PARSER.add_argument('-swid', default='SWID')
    PARSER.add_argument('-websocketdelay', type=int, default=1)
    ARGS = PARSER.parse_args()

    ARGS.league = League(int(os.environ.get(ARGS.espnleague)), 2017, espn_s2=os.environ.get(ARGS.espns2), swid=os.environ.get(ARGS.swid))
    # sc = ARGS.league.scoreboard(projections=True)
    # home_names = '\n'.join(map(lambda x: x.home_team.team_abbrev, sc))
    # home_scores = '\n'.join(map(lambda x: x.home_score, sc))
    # home_proj = '\n'.join(map(lambda x: x.home_projection, sc))
    # print(home_scores)
    # exit()
    
    CLIENT = SlackClient(os.environ.get(ARGS.slacktoken))

    BOTID = getfootballbot(ARGS, CLIENT)


    ARGS.atbot = "<@" + BOTID + ">"

    startloop(ARGS, CLIENT)