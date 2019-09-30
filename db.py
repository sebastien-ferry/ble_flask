import db_password

import psycopg2

def db_connect():
    db_connection = None
    db_cursor = None
    try:
        db_connection = psycopg2.connect( user = db_password_user
                                     , password = db_password_password
                                     , host = db_password_host
                                     , port = db_password_port
                                     , database = db_password_database)
        db_cursor = db_connection.cursor()

    except (Exception, psycopg2.Error) as error :
        print ("ERROR PsycoPG2 (db_connect) : ", error)
        return None, None

    return db_connection, db_cursor

def db_close(db_connection, db_cursor):
    try:
        if (db_cursor):
            db_cursor.close()

        if (db_connection):
            db_connection.close()

    except (Exception, psycopg2.Error) as error :
        print ("ERRO PsycoPG2 (db_close): ", error)

    return

def db_select_device(db_cursor, address=None, address_type=None, limit=10):
    sql = """ select d.*, o.identifier
              from device as d inner join oui as o
                  on  o.prefix = left(d.address, 8)
                  and d.address_type = 'public'
              order by d.lastseen desc"""
    sql += " limit " + str(limit) + " ;"

    db_cursor.execute(sql)
    device = db_cursor.fetchall()
    return device

def db_select_scan(db_cursor):
    sql = """ SELECT * from scan
             order by timestamp desc
             limit 10 ;"""
    db_cursor.execute(sql)
    scan = db_cursor.fetchall()
    return scan

def db_select_scan_data(db_cursor, address=None, address_type=None, limit=None):
    sql = """select *
             from  scan_data
             where 1=1""" #name in ('Short Local Name', 'Complete Local Name')"""
    if address is not None and address_type is not None:
        sql += " and address='" + p_address +"'" \
             + " and address_type ='" + p_address_type +"'"
    sql += " order by timestamp desc, address, address_type, name"
    if limit is not None:
        sql += " limit " + str(limit) + " ;"
    else:
        sql += " limit 30 ;"

    db_cursor.execute(sql)
    scan_data = db_cursor.fetchall()
    return scan_data

def db_select_scan_bucket(db_cursor):
    sql = """select day_hour, coalesce(count(scan.*),0)
    from (	select generate_series(date_trunc('hour', now() - interval '1 day'),now(), '10 min') as day_hour
    	 ) as timeserie
    left outer join scan
    	 on timeserie.day_hour = to_timestamp( (floor(extract(epoch from scan.timestamp at time zone 'UTC-8') / (10*60))*(10*60) ))
    	 --and scan.timestamp > now() - interval '24:00:00'
    group by day_hour"""

    db_cursor.execute(sql)
    scan_data_bucket = db_cursor.fetchall()
    return scan_data_bucket

def db_select_scan_data_car(db_cursor):
    sql = """ SELECT *
              FROM scan_data as s
              WHERE s.value like '沪%'
              order by timestamp desc; """
    db_cursor.execute(sql)
    scan_data_car = db_cursor.fetchall()
    return scan_data_car

def db_select_recap(db_cursor, restrict=None):
    t_queries = {
          'device_total' : """
            select count(1)
            from device"""
        , 'device_delta' : """
            select count(1)
            from device
            where lastseen > now() - interval '1 day'
            """
        , 'device_bucket' : """
            select bucket, coalesce(count(s.*),0)
            FROM (select generate_series(date_trunc('day', now() - interval '7 day'),now(), '1 day')::DATE as bucket) as timeserie
             left  outer join device as s
            	on    timeserie.bucket = date_trunc('day', s.lastseen )
            	and   s.lastseen > now() - interval '7 days'
            group by bucket
            order by bucket
            """
        , 'name_total' : """
            select count(1)
            from scan_data
            where name in ('Complete local Name', 'Short Local Name')
            """
        , 'name_delta' : """
            select count(1)
            from scan_data
            where timestamp > now() - interval '1 day'
            and   name in ('Complete local Name', 'Short Local Name')
            """
        , 'name_bucket' : """
            select bucket, coalesce(count(s.*),0)
            FROM (select generate_series(date_trunc('day', now() - interval '7 day'),now(), '1 day')::DATE as bucket) as timeserie
             left  outer join scan_data as s
            	on    timeserie.bucket = date_trunc('day', s.timestamp )
            	and   s.timestamp > now() - interval '7 days'
                and   name in ('Complete local Name', 'Short Local Name')
            group by bucket
            order by bucket
            """
        , 'scan_total' : """
            select count(1)
            from scan
            """
        , 'scan_delta' : """
            select count(1)
            from scan
            where timestamp > now() - interval '1 day'
            """
        , 'scan_bucket' : """
            select bucket, coalesce(count(s.*),0)
            FROM (select generate_series(date_trunc('day', now() - interval '7 day'),now(), '1 day')::DATE as bucket) as timeserie
             left  outer join scan as s
            	on    timeserie.bucket = date_trunc('day', s.timestamp )
            	and   s.timestamp > now() - interval '7 days'
            group by bucket
            order by bucket
            """
        , 'car_total' : """
            SELECT count(1)
            FROM scan_data as s
            WHERE 1=1
            and   s.address_type = 'public'
            AND   s.name = 'Complete Local Name'
            AND   s.value like '沪%'
            """
        , 'car_delta' : """
            SELECT count(1)
            FROM scan_data as s
            WHERE 1=1
            and   timestamp > now() - interval '1 day'
            and   s.address_type = 'public'
            AND   s.name = 'Complete Local Name'
            AND   s.value like '沪%'
            """
        , 'car_bucket' : """
            select bucket, coalesce(count(s.*),0)
            FROM (select generate_series(date_trunc('day', now() - interval '7 day'),now(), '1 day')::DATE as bucket) as timeserie
             left  outer join scan_data as s
            	on    timeserie.bucket = date_trunc('day', s.timestamp )
            	and   s.timestamp > now() - interval '7 days'
            	and   s.address_type = 'public'
            	AND   s.name = 'Complete Local Name'
            	AND   s.value like '沪%'
            group by bucket
            order by bucket
            """
            }
    t_result = {}
    for name, query in t_queries.items():
        if restrict is None or name in restrict:
            db_cursor.execute(query)
            result = db_cursor.fetchall()
            if db_cursor.rowcount == 1:
                t_result[name] = "{:,}".format(result[0][0])
            else:
                t_result[name] = result

    return t_result

def db_select_word_cloud(db_cursor):
    t_queries = {
          'name' : """
            select value,  count(1)
            from scan_data
            where name in ('Short Local Name', 'Complete Local Name')
            group by value
            having count(1) > 1
            order by count(1) desc
            limit 100
            """
        , 'manufacturer' : """
            select identifier, count(1)
            from device
            inner join oui
            on    prefix = left(address, 8)
            and   address_type = 'public'
            group by identifier
            having count(1) > 1
            order by count(1) desc, identifier
            limit 100
            """
        }

    t_result = {}
    for name, query in t_queries.items():
        db_cursor.execute(query)
        result = db_cursor.fetchall()
        t_result[name] = result

    return t_result
