"""modified from https://github.com/wkentaro/gdown/blob/main/gdown/download.py"""
from regex import search
from gdown.download import _get_session, parse_url, get_url_from_gdrive_confirmation, indent, textwrap, FileURLRetrievalError, MozillaCookieJar


def google_drive(
    url=None,
    proxy=None,
    use_cookies=True,
    verify=True,
    id=None,
    fuzzy=False,
    format=None,
    user_agent=None,
    log_messages=None,
):
    """Parse direct link from Google Drive.

    Parameters
    ----------
    url: str
        URL. Google Drive URL is also supported.
    output: str
        Output filename/directory. Default is basename of URL.
        If output ends with separator '/' basename will be kept and the
        parameter will be treated as parenting directory.
    quiet: bool
        Suppress terminal output. Default is False.
    proxy: str
        Proxy.
    speed: float
        Download byte size per second (e.g., 256KB/s = 256 * 1024).
    use_cookies: bool
        Flag to use cookies. Default is True.
    verify: bool or string
        Either a bool, in which case it controls whether the server's TLS
        certificate is verified, or a string, in which case it must be a path
        to a CA bundle to use. Default is True.
    id: str
        Google Drive's file ID.
    fuzzy: bool
        Fuzzy extraction of Google Drive's file Id. Default is False.
    resume: bool
        Resume interrupted downloads while skipping completed ones.
        Default is False.
    format: str, optional
        Format of Google Docs, Spreadsheets and Slides. Default is:
            - Google Docs: 'docx'
            - Google Spreadsheet: 'xlsx'
            - Google Slides: 'pptx'
    user_agent: str, optional
        User-agent to use in the HTTP request.
    log_messages: dict, optional
        Log messages to customize. Currently it supports:
        - 'start': the message to show the start of the download
        - 'output': the message to show the output filename

    Returns
    -------
    output: str
        Output filename.
    """
    if not (id is None) ^ (url is None):
        raise ValueError("Either url or id has to be specified")
    if id is not None:
        url = "https://drive.google.com/uc?id={id}".format(id=id)
    if user_agent is None:
        # We need to use different user agent for file download c.f., folder
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"  # NOQA: E501
    if log_messages is None:
        log_messages = {}

    url_origin = url

    sess, cookies_file = _get_session(
        proxy=proxy,
        use_cookies=use_cookies,
        user_agent=user_agent,
        return_cookies_file=True,
    )

    gdrive_file_id, is_gdrive_download_link = parse_url(url, warning=not fuzzy)

    if fuzzy and gdrive_file_id:
        # overwrite the url with fuzzy match of a file id
        url = "https://drive.google.com/uc?id={id}".format(id=gdrive_file_id)
        url_origin = url
        is_gdrive_download_link = True

    while True:
        res = sess.get(url, stream=True, verify=verify)

        if not (gdrive_file_id and is_gdrive_download_link):
            break

        if url == url_origin and res.status_code == 500:
            # The file could be Google Docs or Spreadsheets.
            url = "https://drive.google.com/open?id={id}".format(id=gdrive_file_id)
            continue

        if res.headers["Content-Type"].startswith("text/html"):
            m = search("<title>(.+)</title>", res.text)
            if m and m.groups()[0].endswith(" - Google Docs"):
                url = (
                    "https://docs.google.com/document/d/{id}/export"
                    "?format={format}".format(
                        id=gdrive_file_id,
                        format="docx" if format is None else format,
                    )
                )
                continue
            elif m and m.groups()[0].endswith(" - Google Sheets"):
                url = (
                    "https://docs.google.com/spreadsheets/d/{id}/export"
                    "?format={format}".format(
                        id=gdrive_file_id,
                        format="xlsx" if format is None else format,
                    )
                )
                continue
            elif m and m.groups()[0].endswith(" - Google Slides"):
                url = (
                    "https://docs.google.com/presentation/d/{id}/export"
                    "?format={format}".format(
                        id=gdrive_file_id,
                        format="pptx" if format is None else format,
                    )
                )
                continue
        elif (
            "Content-Disposition" in res.headers
            and res.headers["Content-Disposition"].endswith("pptx")
            and format not in {None, "pptx"}
        ):
            url = (
                "https://docs.google.com/presentation/d/{id}/export"
                "?format={format}".format(
                    id=gdrive_file_id,
                    format="pptx" if format is None else format,
                )
            )
            continue

        if use_cookies:
            cookie_jar = MozillaCookieJar(cookies_file)
            for cookie in sess.cookies:
                cookie_jar.set_cookie(cookie)
            cookie_jar.save()

        if "Content-Disposition" in res.headers:
            # This is the file
            break

        # Need to redirect with confirmation
        try:
            url = get_url_from_gdrive_confirmation(res.text)
        except FileURLRetrievalError as e:
            message = (
                "Failed to retrieve file url:\n\n{}\n\n"
                "You may still be able to access the file from the browser:"
                "\n\n\t{}\n\n"
                "but Gdown can't. Please check connections and permissions."
            ).format(
                indent("\n".join(textwrap.wrap(str(e))), prefix="\t"),
                url_origin,
            )
            raise FileURLRetrievalError(message)

    return res.url
