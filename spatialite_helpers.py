import sqlite3
from string import Template
from typing import Optional
import shapely.wkb as swkb


def load_spatialite(gdf, name: str, con: sqlite3.Connection, if_exists: str = 'fail', 
                     index: bool = True, index_label=None, chunksize=None, dtype=None, 
                     method=None, srid: int = 4326, id_field: str = None) -> None:

    temp_df = gdf.drop(['geometry'], axis=1)
    temp_df.to_sql(name=name, con=con, if_exists=if_exists, index=index, index_label=index_label, chunksize=chunksize,
                   dtype=dtype, method=method)
    
    
    geom_type = gdf.geometry.type[0]
    wkb = gdf.geometry.apply(swkb.dumps)
    
    if id_field:
        pass
    elif index_label:
        id_field = index_label
    elif temp_df.index.name == None:
        id_field = 'index'
    else:
        id_field = temp_df.index.name
        
    con.execute(
    f"""
    SELECT AddGeometryColumn(null,'{name}', 'geometry',  {srid}, '{geom_type.lower()}', 'XY', 'null');
    """)
        
    tuples = tuple(zip(wkb, gdf[id_field]))
    
    con.executemany(
    f"""
    UPDATE {name}
    SET geometry=st_polyfromwkb(?, {srid})
    WHERE {name}.{id_field} = ?;
    """, (tuples)
    )



    
def create_spatialite_db(connection:sqlite3.Connection, spatialite_binary: Optional[str]=None) -> sqlite3.Connection:

    from string import Template
    
    
    connection.enable_load_extension(True)

    platform = {'nt': 'stgeometry_sqlite.dll', 'linux': 'stgeometry_sqlite.so'}
    load_ext = "SELECT load_extension('$platform','SDE_SQL_funcs_init');"

    if os.name == 'nt':
        load_ext_sql = Template(load_ext).substitute(platform=platform['nt'])
        connection.execute(load_ext_sql)
    else:
        load_ext_sql = Template(load_ext).substitute(platform=platform['linux'])
        connection.execute(load_ext_sql)
    connection.execute("select CreateOGCTables()")
    return connection

con = sqlite3.connect(r'D:\Python\testsqlite_1.sqlite')
con = create_spatialite_db(con)
load_spatialite(gdf, 'test_table16', con, id_field='osm_id')
read_df = gpd.read_postgis("SELECT *, ST_AsBinary(geometry) as geom  from test_table16", con)