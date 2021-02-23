from fastapi import APIRouter, Depends
from driveapi import files


router = APIRouter()

@router.get('/api/integ/gdrive/notifications')
def process_notification(db_app: Session = Depends(access.get_app_db), db_data: Session = Depends(access.get_data_db)):
    fiels.update_user_file_records(db_app=db_app, db_data=db_data)