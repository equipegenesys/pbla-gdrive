def mimetype_mapper(original_mimetype: str):

    mimetypes = {'application/vnd.google-apps.document': google_document, 
                'application/vnd.google-apps.spreadsheet': google_sheets, 
                'application/vnd.google-apps.drawing': google_drawing, 
                'application/vnd.google-apps.presentation': google_slides}

    if original_mimetype in mimetypes:
        converted_mimetype = mimetypes[f'{original_mimetype}']    
        return converted_mimetype
    return False


def google_document():
    return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

def google_sheets():
    return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

def google_slides():
    return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'

def google_drawing():
    return 'image/png' 