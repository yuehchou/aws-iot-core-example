import os
import sys
import threading
from uuid import uuid4
from awscrt import mqtt
from command_line_utils import CommandLineUtils

RECEIVED_ALL_EVENT = threading.Event()


def get_cmd() -> CommandLineUtils:
    """
    """
    cmd_utils = CommandLineUtils("Subscription - recieve message through an MQTT connection.")
    cmd_utils.add_common_mqtt_commands()
    cmd_utils.add_common_proxy_commands()
    cmd_utils.add_common_logging_commands()
    cmd_utils.register_command(
        command_name="topic",
        example_input="<str>",
        help_output="Topic to publish, subscribe to (optional, default='test/topic').",
        default="test/topic"
    )
    cmd_utils.register_command(
        command_name="key",
        example_input="<path>",
        help_output="Path to your key in PEM format.",
        required=True,
        type=str
    )
    cmd_utils.register_command(
        command_name="cert",
        example_input="<path>",
        help_output="Path to your client certificate in PEM format.",
        required=True,
        type=str
    )
    cmd_utils.register_command(
        command_name="port",
        example_input="<int>",
        help_output="Connection port. AWS IoT supports 443 and 8883 (optional, default=auto).",
        type=int
    )
    cmd_utils.register_command(
        command_name="client_id",
        example_input="<str>",
        help_output="Client ID to use for MQTT connection (optional, default='test-*').",
        default=f"test-{str(uuid4())}"
    )
    cmd_utils.register_command(
        command_name="is_ci",
        example_input="<str>",
        help_output="If present the sample will run in CI mode (optional, default='None')"
    )
    cmd_utils.get_args()
    return cmd_utils


def on_connection_interrupted(
        connection,
        error,
        **kwargs
):
    print("Connection interrupted. error: {}".format(error))


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(
                topic))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(
        connection,
        return_code,
        session_present,
        **kwargs
):
    print("Connection resumed. return_code: {} session_present: {}".format(
        return_code,
        session_present
    ))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    """
        Can add the action to deal with payload
    """
    if isinstance(payload, bytes):
        os.system(f"python pyload_analysis.py -m {payload.decode('utf-8')}")
    elif isinstance(payload, str):
        os.system(f"python pyload_analysis.py -m {payload}")


if __name__ == '__main__':
    cmd_utils = get_cmd()
    mqtt_connection = cmd_utils.build_mqtt_connection(
        on_connection_interrupted,
        on_connection_resumed
    )

    is_ci = cmd_utils.get_command("is_ci", None)
    if not is_ci:
        print("Connecting to {} with client ID '{}'...".format(
            cmd_utils.get_command(cmd_utils.m_cmd_endpoint),
            cmd_utils.get_command("client_id")
        ))
    else:
        print("Connecting to endpoint with client ID")
    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    message_topic = cmd_utils.get_command("topic")

    # Subscribe
    print("Subscribing to topic '{}'...".format(message_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=message_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received
    )

    print("Start to receive messages...")
    RECEIVED_ALL_EVENT.wait()
