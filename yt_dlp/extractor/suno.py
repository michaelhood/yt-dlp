from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    traverse_obj,
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

        # Extract audio URL directly from the content (most reliable)
        # Pattern found in the JSON data embedded in the page
        audio_url = self._search_regex(
            r'audio_url.*?([^"\']+\.mp3)', webpage, 'audio url', default=None)
        
        # Extract duration from the JSON data  
        duration = None
        duration_match = self._search_regex(
            r'duration.*?([0-9.]+)', webpage, 'duration', default=None)
        if duration_match:
            try:
                duration = float(duration_match)
            except ValueError:
                pass
        
        # Extract uploader from display_name in the clip data (with escaped quotes)
        uploader = self._search_regex(
            r'display_name\\":\\"([^\\"]+)\\"', webpage, 'uploader', default=None)
        
        # Extract title from the clip data (with escaped quotes)
        title = self._search_regex(
            r'title\\":\\"([^\\"]+)\\"', webpage, 'title from clip', default=None)
        
        # Clean up title if it includes site name
        if title:
            title = title.replace(' | Suno', '').strip()
        
        # Extract description from og:description in metadata (with escaped quotes)
        description = self._search_regex(
            r'\\\"og:description\\\"[^\\\"]*\\\"content\\\":\\\"([^\\\"]+)\\\"', webpage, 'description from og', default=None)
        
        if not audio_url:
            raise ExtractorError(
                'Unable to find audio URL. The page structure may have changed.',
                expected=True)
        
        return {
            'id': video_id,
            'title': title or video_id,
            'description': description,
            'url': audio_url,
            'ext': 'mp3',  # Default extension, may be auto-detected from URL
            'duration': duration,
            'uploader': uploader,
            'vcodec': 'none',  # Audio-only content
        }