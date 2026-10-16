from src.utils.helpers.files import FilesHelper


def test_media_type_for_known_extensions():
    assert FilesHelper.media_type_for("photo.png") == "image/png"
    assert FilesHelper.media_type_for("notes.txt") == "text/plain; charset=utf-8"
    assert FilesHelper.media_type_for("archive.zip") == "application/zip"


def test_executable_content_is_served_as_download():
    # html/js/svg не должны исполняться в контексте приложения (stored XSS)
    assert FilesHelper.media_type_for("evil.html") == "application/octet-stream"
    assert FilesHelper.media_type_for("evil.js") == "application/octet-stream"
    assert FilesHelper.media_type_for("evil.svg") == "application/octet-stream"
    assert FilesHelper.media_type_for("no-extension") == "application/octet-stream"
