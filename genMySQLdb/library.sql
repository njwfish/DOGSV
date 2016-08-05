create table queries (
id mediumint(8) unsigned not null auto_increment comment 'The unique identifier of this query, used for reference.',
time timestamp DEFAULT CURRENT_TIMESTAMP comment 'Time of search of this query.',
query varchar(4000) comment 'The text of the query.',
time_elapsed mediumint(8) unsigned comment 'The time elapsed during the query in milliseconds.',
primary key(id)) comment = 'The list of queries.'

create table keywords (
id mediumint(8) unsigned not null comment 'The unique identifier of this query, used for reference.',
kw1 varchar(500) comment 'A keyword for searches.',
kw2 varchar(500) comment 'A keyword for searches.',
kw3 varchar(500) comment 'A keyword for searches.',
kw4 varchar(500) comment 'A keyword for searches.',
kw5 varchar(500) comment 'A keyword for searches.',
primary key(id), 
foreign key fk_id(id) references queries(id)) comment = 'Keeps a list of 5 possible key words for a given query.'