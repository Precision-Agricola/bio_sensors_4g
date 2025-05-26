# server/mqtt_commands/base.py

class MQTTCommand:
    def handle(self, payload, topic):
        """
        Ejecuta el comando con los datos recibidos.

        Parameters:
            payload (dict): contenido del mensaje.
            topic (str): tópico MQTT desde donde fue recibido.
        """
        raise NotImplementedError("Debe implementar el método handle()")
