import contextlib
import time
from std_logger import logger

def split_seconds(seconds):
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return hours, minutes, seconds

def format_seconds(seconds):
    hours, minutes, seconds = split_seconds(seconds)
    ll = []
    pf = "s" if hours > 1 else ""
    if hours:
        ll.append("%d hour%s" % (hours, pf))
    pf = "s" if minutes > 1 else ""
    if hours and minutes:
        ll.append(", %d minute%s" % (minutes, pf))
    elif minutes:
        ll.append("%d minute%s" % (minutes, pf))
    if hours or minutes:
        ll.append(" and %.2f seconds" % seconds)
    else:
        ll.append("%.2f seconds" % seconds)
    return "".join(ll)


def format_seconds(seconds):
    hours, minutes, seconds = split_seconds(seconds)
    ll = []
    pf = "s" if hours > 1 else ""
    if hours:
        ll.append("%d hour%s" % (hours, pf))
    pf = "s" if minutes > 1 else ""
    if hours and minutes:
        ll.append(", %d minute%s" % (minutes, pf))
    elif minutes:
        ll.append("%d minute%s" % (minutes, pf))
    if hours or minutes:
        ll.append(" and %.2f seconds" % seconds)
    else:
        ll.append("%.2f seconds" % seconds)
    return "".join(ll)


def split_bytes(bytes_):
    gb, bytes_ = divmod(bytes_, 1024 * 1024 * 1024)
    mb, bytes_ = divmod(bytes_, 1024 * 1024)
    kb = bytes_ / 1024.0
    return gb, mb, kb


def format_bytes(bytes_):
    gb, mb, kb = split_bytes(bytes_)
    ll = []
    if gb:
        ll.append("%d GB" % gb)
    if mb and gb:
        ll.append(", %d MB" % mb)
    elif mb:
        ll.append("%d MB" % mb)
    if mb or gb:
        ll.append(" and %.1f KB" % kb)
    else:
        ll.append("%.1f KB" % kb)
    return "".join(ll)


@contextlib.contextmanager
def measure_time(job_description):
    start_at = time.time()
    logger.info("start %s" % job_description)
    yield
    needed = time.time() - start_at
    logger.info("%s needed %s" % (job_description, format_seconds(needed)))


if __name__ == "__main__":
    print format_seconds(3)
    print format_seconds(3.2)
    print format_seconds(60)
    print format_seconds(120)
    print format_seconds(121)
    print format_seconds(3 + 60)
    print format_seconds(3600)
    print format_seconds(7200)
    print format_seconds(3600 + 3)
    print format_seconds(3600 + 60 )
    print format_seconds(3600 + 60 + 3.3)
    print format_seconds(7200 + 3)
    print format_seconds(7200 + 60 )
    print format_seconds(3600 + 60 + 3.3)

    print format_bytes(1000.0)
    print format_bytes(1024.0)
    print format_bytes(2 * 1024.0)
    print format_bytes(1024 * 1024)
    print format_bytes(1024 * 1024 + 2* 1024)
    print format_bytes(1024 * 1024 * 1024)
    print format_bytes(2.3 * 1024 * 1024 * 1024)
