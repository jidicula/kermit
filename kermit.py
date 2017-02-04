import os, time, re, urllib2, twitter, sys
from slackclient import SlackClient
from bs4 import BeautifulSoup

# atlas's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"

# instantiate Slack client
slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    if command.lower().startswith("hi"):
        response = "What's up?"
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        return

    if command.lower().startswith("bye"):
        response = "Goodbye!"
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        return

    if re.match(r"help",command.lower()):
        response = help()
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        return

    if command.lower().startswith("tweet"):
        response = tweet(command)
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        return
    if command.lower().startswith("weather"):
        response = current_weather()
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        return

    if command.lower().startswith("restart"):
        response = "Restarting... https://streamable.com/dli1"
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        restart_program()
        return

    if command.lower().startswith("die"):
        response = "http://i.imgur.com/g3Qk9gQ.gifv"
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
        sys.exit()
        return

    else:
        response = "Not a valid command. Use `@atlas help` to get a list of commands. https://streamable.com/foljj"
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

def tweet(command):
    content = str(command).replace("tweet ","").strip("'")
    # Receives links in the form: <mailto:macss.academic@gmail.com|macss.academic@gmail.com> or as <https://macssmcgill.github.io/services.html>
    content = re.sub(r"\|.*>","",content)
    content = re.sub(r"<(mailto:|https?:\/\/(w{3}\.)?)","",content)
    content = content.replace("&amp;","&")
    if len(content)>140:
        confirm = u"Tweet failed: longer than 140 characters. Length = %s" % (len(content))
    else:
        api = twitter.Api(consumer_key=os.environ.get("TWITTER_CONSUMER_KEY"),consumer_secret=os.environ.get("TWITTER_CONSUMER_SECRET"),access_token_key=os.environ.get("TWITTER_ACCESS_TOKEN"),access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"))
        status = api.PostUpdate(content)
        confirm = "*Tweeted:* " + status.text
    return confirm

def current_weather():
    url = urllib2.urlopen("http://weather.gc.ca/city/pages/qc-147_metric_e.html")
    soup = BeautifulSoup(url, "html.parser")
    # Get date
    observed_label = soup.find("dt",string="Date: ")
    observed = observed_label.find_next_sibling().get_text().rstrip()
    # Get temperature
    temperature_label = soup.find("dt",string="Temperature:")
    temperature = temperature_label.find_next_sibling().get_text().strip()
    # Get condition
    condition_label = soup.find("dt",string="Condition:")
    condition = condition_label.find_next_sibling().get_text().strip()
    # Get pressure
    pressure_label = soup.find("dt",string="Pressure:")
    pressure = pressure_label.find_next_sibling().get_text().strip()
    # Get tendency
    tendency_label = soup.find("dt",string="Tendency:")
    tendency = tendency_label.find_next_sibling().get_text().strip()
    # Get wind
    wind_label = soup.find("dt",string="Wind:")
    wind = wind_label.find_next_sibling().get_text().strip()
    windchill = u"N/A"
    try:
        # Get windchill, only if it can be found.
        windchill_label = soup.find("a",string="Wind Chill")
        windchill = windchill_label.find_next().get_text().strip() + u"\xb0C"
    except:
        pass

    weather_now = u"Conditions observed at: *%s*.\nTemperature: *%s*\nCondition: *%s*\nPressure: *%s*\nTendency: *%s*\nWind speed: *%s*\nWind chill: *%s*" % (observed,temperature,condition,pressure,tendency,wind,windchill)
    return weather_now

def help():
    commandlist = """
                    `@atlas tweet 'CONTENTS OF TWEET'`\n`@atlas ntc anat262 status`\n`@atlas ntc anat262 update 1 ready` or `@atlas ntc anat262 update 1 in progress`\n`@atlas weather`\n`@atlas restart`
                    """
    return commandlist

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and "text" in output and AT_BOT in output["text"]:
                # return text after the @ mention, whitespace removed
                return output["text"].split(AT_BOT)[1].strip(), \
                       output["channel"]
    return None, None

def restart_program():
    """Restarts the current program, with file objects and descriptors
       cleanup
    """

    python = sys.executable
    os.execl(python, python, *sys.argv)

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("ATLAS connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
