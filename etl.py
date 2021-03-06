import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    """function for handling and inserting song data"""
    # open song file
    df = pd.read_json(filepath,lines=True)

    # insert song record
    song_data = tuple(df[['song_id','title','artist_id','year','duration']].values[0])
    #print(song_table_insert+"||| "+str(song_data))
    cur.execute(song_table_insert, song_data)
    
    # insert artist record
    artist_data = tuple(df[['artist_id','artist_name','artist_location','artist_latitude','artist_longitude']].values[0])
    cur.execute(artist_table_insert, artist_data)

def process_log_file(cur, filepath):
    """function for handling and inserting LOG data"""
    # open log file
    df = pd.read_json(filepath,lines=True)

    # filter by NextSong action
    df=df[df['page']=='NextSong']

    # convert timestamp column to datetime
    t = pd.to_datetime(df['ts'], unit='ms')
    
    # insert time data records
    time_data = [t,t.dt.hour,t.dt.day,t.dt.week,t.dt.month,t.dt.year,t.dt.weekday]
    column_labels = ['Time','Hours','Day','Week','Month','Year','Weekday']
    time_df = pd.concat(time_data,axis=1)
    time_df.columns=column_labels

    for i, row in time_df.iterrows():
        #print(time_table_insert+"||| "+str(list(row)))
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[['userId','firstName','lastName','gender','level']]

    # insert user records
    for i, row in user_df.iterrows():
        if not list(row)[0]=="":
                cur.execute(user_table_insert, row)               
        else:
             print("empty user_id.Record will be ignored..")

    # insert songplay records
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        #print(str(row.song), str(row.artist), str(row.length))
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        time=str(pd.to_datetime(row.ts, unit='ms').time())
        songplay_data =(time,row.userId,row.level,songid,artistid,row.sessionId,row.location,row.userAgent) 
        if not songid==None:
            print("songid found "+str(songid))
            cur.execute(songplay_table_insert, songplay_data)
            #conn.commit()
        else:
            print("No songid found for: "+str(row.song) +" AND "+ str(row.artist)+" AND "+str(row.length))   



def process_data(cur, conn, filepath, func):
    """Scan and process all json files:songs and logs"""
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()