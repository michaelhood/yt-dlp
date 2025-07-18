from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    url_or_none,
)


class SunoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?suno\.com/embed/(?P<id>[a-zA-Z0-9_-]+)$'
    _TESTS = [{
        'url': 'https://suno.com/embed/afc9a71f-7687-4410-94a7-b6dd45418ab8',
        'info_dict': {
            'id': 'afc9a71f-7687-4410-94a7-b6dd45418ab8',
            'ext': 'mp3',
            'title': "It's Pronounced GIF! [SSC5, USA]",
            'description': 'Listen and make your own on Suno.',
            'duration': 152.64,
            'uploader': 'themightytruk',
            'vcodec': 'none',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Extract audio URL using multiple fallback patterns
        audio_url = (
            self._search_regex(
                r'audio_url["\']:["\']\s*([^"\']+\.mp3)', webpage, 'audio url', default=None)
            or self._search_regex(
                r'"audioUrl":\s*"([^"]+\.mp3)"', webpage, 'audio url alt', default=None)
            or self._search_regex(
                r'<audio[^>]+src=["\']\s*([^"\']+\.mp3)', webpage, 'audio url from tag', default=None)
        )

        # Extract duration with better error handling
        duration = float_or_none(self._search_regex(
            r'duration["\']?\s*:\s*([0-9.]+)', webpage, 'duration', default=None))

        # Extract uploader with multiple fallback patterns
        uploader = (
            self._search_regex(
                r'display_name\\?["\']:\s*\\?["\']([^"\'\\]+)\\?["\']', webpage, 'uploader', default=None)
            or self._search_regex(
                r'"uploader":\s*"([^"]+)"', webpage, 'uploader alt', default=None)
        )

        # Extract title with multiple fallback patterns
        title = (
            self._search_regex(
                r'title\\?["\']:\s*\\?["\']([^"\'\\]+)\\?["\']', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or self._html_search_meta('title', webpage, default=None)
        )

        # Clean up title if it includes site name
        if title:
            title = title.replace(' | Suno', '').strip()

        # Extract description with multiple fallback patterns
        description = (
            self._search_regex(
                r'\\?["\']og:description\\?["\'][^"\']*\\?["\']content\\?["\']:\s*\\?["\']([^"\'\\]+)\\?["\']',
                webpage, 'description', default=None)
            or self._og_search_description(webpage, default=None)
            or self._html_search_meta('description', webpage, default=None)
        )

        # Ensure we have a valid audio URL
        audio_url = url_or_none(audio_url)
        if not audio_url:
            raise ExtractorError(
                'Unable to find audio URL. The page structure may have changed.',
                expected=True)

        return {
            'id': video_id,
            'title': title or video_id,
            'description': description,
            'url': audio_url,
            'ext': 'mp3',
            'duration': duration,
            'uploader': uploader,
            'vcodec': 'none',
        }
