from backend.app.db.migrations import initialize_database

if __name__ == '__main__':
    initialize_database()
    print('PostGIS extension and scaffold tables initialized')
