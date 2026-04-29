import os
import sentry_sdk
from app.main import app

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    send_default_pii=True,
    traces_sample_rate=1.0,
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)