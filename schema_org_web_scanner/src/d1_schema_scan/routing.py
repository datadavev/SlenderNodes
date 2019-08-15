import channels.auth
import channels.routing

import d1_schema_scan.app.consumers
import d1_schema_scan.app.routing

application = channels.routing.ProtocolTypeRouter(
    {
        "websocket": channels.auth.AuthMiddlewareStack(
            channels.routing.URLRouter(d1_schema_scan.app.routing.websocket_urlpatterns)
        ),
        "channel": channels.routing.ChannelNameRouter(
            {"scan": d1_schema_scan.app.consumers.ScannerConsumer}
        ),
    }
)
