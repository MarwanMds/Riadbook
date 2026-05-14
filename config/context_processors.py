def html_direction(request):
    lang = getattr(request, 'LANGUAGE_CODE', 'fr')
    return {'html_dir': 'rtl' if lang == 'ar' else 'ltr'}