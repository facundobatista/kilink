import psycopg2

with open("project/production/configs/db_auth.txt") as fh:
    vals = [x.strip() for x in fh.readlines()]
auth_data = dict(zip(("user", "pass"), vals))

con = psycopg2.connect("dbname=kilink user={user} password={pass} host=localhost".format(**auth_data))
cur = con.cursor()
cur.execute("drop table if exists kilink_new;")
con.commit()

create_table = """
CREATE TABLE kilink_new (
    linkode_id character varying NOT NULL primary key,
    root character varying NOT NULL,
    parent character varying,
    compressed bytea,
    "timestamp" timestamp without time zone,
    text_type character varying DEFAULT ''::character varying
);"""

cur.execute(create_table)
con.commit()

q_root_nodes = """
SELECT kid, revno, parent, compressed, timestamp, text_type from kilink where parent is NULL;
"""

q_first_child_node = """
SELECT kid, revno, parent, compressed, timestamp, text_type 
from kilink 
where parent = %s"""

q_rest_child_node = """
SELECT kid, revno, parent, compressed, timestamp, text_type 
from kilink 
where kid=%s and parent != %s and parent is not null"""

q_insert = """
INSERT into kilink_new (linkode_id, root, parent, compressed, timestamp, text_type) 
values (%s,%s,%s,%s,%s,%s)"""

cur.execute(q_root_nodes)
root_nodes = cur.fetchall()

for r_kid, r_revno, r_parent, r_compressed, r_timestamp, r_text_type in root_nodes:
    print "=============================Root ", r_kid, r_revno, r_parent, "=============="
    cur.execute(q_insert, (r_kid, r_kid, r_parent, r_compressed, r_timestamp, r_text_type))

    cur.execute(q_first_child_node, (r_revno,))
    first_children = cur.fetchall()
    for kid, revno, parent, compressed, timestamp, text_type in first_children:
        print "=============================First One ", kid, revno, parent, "=============="
        cur.execute(q_insert, (revno, kid, kid, compressed, timestamp, text_type))

    cur.execute(q_rest_child_node, (r_kid, r_revno))
    rest_children = cur.fetchall()
    for kid, revno, parent, compressed, timestamp, text_type in rest_children:
        print "=============================Rest ", kid, revno, parent, "=============="
        cur.execute(q_insert, (revno, kid, parent, compressed, timestamp, text_type))

    con.commit()
