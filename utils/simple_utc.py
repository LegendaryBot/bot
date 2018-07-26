from datetime import tzinfo, timedelta


class simple_utc(tzinfo):
    def tzname(self, **kwargs):
        return "UTC"

    def utcoffset(self, dt):
        return timedelta(0)
