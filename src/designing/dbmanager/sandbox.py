from src.designing.dbmanager.constants import URI, PASSWORD, USER, DB
from src.designing.dbmanager.dbmanager import DBManager

dbm = DBManager(uri=URI, auth=(USER, PASSWORD))

dbm.run("""
CREATE 
    (alice:User {name: 'Alice', age: 30}),
    (bob:User {name: 'Bob', age: 25}),
    (charlie:User {name: 'Charlie', age: 35}),
    (post1:Post {title: 'Hello World'}),
    (post2:Post {title: 'Neo4j Rocks'}),
    (tech:Topic {name: 'Tech'}),
    (intro:Topic {name: 'Introduction'}),
    
    (alice)-[:KNOWS {since: 2020}]->(bob),
    (bob)-[:KNOWS {since: 2021}]->(charlie),
    (alice)-[:LIKED {on: date()}]->(post1),
    (bob)-[:LIKED {on: date()}]->(post2),
    (post1)-[:TAGGED]->(tech),
    (post1)-[:TAGGED]->(intro),
    (post2)-[:TAGGED]->(tech)
""")

with dbm.driver.session(database=DB) as session:

    result = session.run("MATCH (u:User) RETURN u.name AS name, u.age AS age")
    pass
    result = session.run("""
        MATCH path=(u:User)-[:KNOWS*]->(friend:User)
        RETURN path
    """).to_eager_result()
    pass
    print(f'n_paths: {len(result.records)}')
    for record in result.records:
        print(
            f"{record['hops']}: ",
            f"{str([node['name'] for node in record['path'].nodes]):<30}",
            f"{str([rel['since'] for rel in record['path'].relationships]):<30}",
        )


dbm.run('MATCH (n) DETACH DELETE n')
