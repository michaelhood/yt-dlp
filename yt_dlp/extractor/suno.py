from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    traverse_obj,
    url_or_none,
)


class SunoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?suno\.com/embed/(?P<id>[0-9a-f-]+)'
    _TESTS = [{
        'url': 'https://suno.com/embed/afc9a71f-7687-4410-94a7-b6dd45418ab8',
        'info_dict': {
            'id': 'afc9a71f-7687-4410-94a7-b6dd45418ab8',
            'ext': 'mp3',
            'title': str,
            'description': str,
            'duration': int,
            'uploader': str,
        },
        'skip': 'Requires access to Suno embed page to extract actual metadata',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Extract title from page title or h1 tag
        title = (self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', default=None) or
            self._html_search_regex(
                r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=None))
        
        # Clean up title if it includes site name
        if title:
            title = title.replace(' | Suno', '').strip()
        
        # Extract description from meta tags
        description = (self._og_search_description(webpage, default=None) or
                      self._html_search_meta('description', webpage, default=None))
        
        # Look for JSON-LD structured data
        json_ld = self._search_json_ld(webpage, video_id, default=None)
        
        # Look for application/json script tags or embedded data
        json_data = self._search_regex(
            [r'<script[^>]+type=["\']application/json["\'][^>]*>([^<]+)</script>',
             r'(?s)<script[^>]*>\s*(?:window\.__INITIAL_STATE__\s*=|window\.__DATA__\s*=|var\s+initialData\s*=)\s*({.+?});?\s*</script>'],
            webpage, 'json data', default=None)
        
        # Parse JSON data if found
        audio_url = None
        duration = None
        uploader = None
        
        if json_data:
            try:
                data = self._parse_json(json_data, video_id, fatal=False)
                if data:
                    # Extract audio URL from various possible locations in JSON
                    audio_url = traverse_obj(data, (
                        ('audio_url', 'audioUrl', 'url', 'src'),
                        {url_or_none}
                    ))
                    duration = traverse_obj(data, (
                        ('duration', 'length', 'duration_seconds'),
                        {int_or_none}
                    ))
                    uploader = traverse_obj(data, (
                        ('artist', 'creator', 'uploader', 'user', 'username'),
                        {str_or_none}
                    ))
                    # Override title from JSON if available and more detailed
                    json_title = traverse_obj(data, (
                        ('title', 'name', 'track_name'),
                        {str_or_none}
                    ))
                    if json_title and len(json_title) > len(title or ''):
                        title = json_title
            except Exception as e:
                self.report_warning(f'Failed to parse JSON data: {e}')
        
        # Look for audio/source tags in HTML
        if not audio_url:
            audio_url = self._html_search_regex(
                [r'<audio[^>]+src=["\']([^"\']+)["\']',
                 r'<source[^>]+src=["\']([^"\']+)["\'][^>]*type=["\']audio/',
                 r'data-audio-url=["\']([^"\']+)["\']'],
                webpage, 'audio url', default=None)
        
        # Extract additional metadata from meta tags
        if not uploader:
            uploader = (self._html_search_meta('author', webpage, default=None) or
                       self._html_search_regex(
                           r'(?i)(?:artist|creator|by)[:\s]*([^<\n]+)', 
                           webpage, 'uploader', default=None))
        
        if not audio_url:
            raise ExtractorError(
                'Unable to find audio URL. The page structure may have changed.',
                expected=True)
        
        # Handle relative URLs
        if audio_url and not audio_url.startswith('http'):
            audio_url = f'https://suno.com{audio_url}'
        
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