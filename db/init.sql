CREATE TABLE creator (
    creator_id SERIAL PRIMARY KEY,
    creator_name VARCHAR ( 100 ) UNIQUE NOT NULL,
    creator_pass VARCHAR ( 256 ),
    creator_role VARCHAR ( 10 ),
    creator_img VARCHAR ( 384 )
);

CREATE TABLE world (
    world_id SERIAL PRIMARY KEY,
    creator_id INT REFERENCES creator ( creator_id ),
    world_name VARCHAR ( 100 ) UNIQUE NOT NULL,
    world_desc VARCHAR ( 1024 ),
    world_url VARCHAR ( 256 ),
    world_img VARCHAR ( 384 )
);

CREATE TABLE room (
    room_id SERIAL PRIMARY KEY,
    world_id INT REFERENCES world ( world_id ),
    room_name VARCHAR ( 100 ),
    room_desc VARCHAR ( 1024 ),
    room_img VARCHAR ( 384) 
);

CREATE UNIQUE INDEX idx_room_name
ON room ( room_name, world_id );

CREATE TABLE item (
    item_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES room ( room_id ),
    world_id INT REFERENCES world ( world_id ),
    item_name VARCHAR ( 100 ),
    item_desc VARCHAR ( 1024 ),
    item_img VARCHAR ( 384 )
);

CREATE UNIQUE INDEX idx_item_name
ON item ( item_name, world_id );

CREATE TABLE objective (
    objective_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES room ( room_id ),
    world_id INT REFERENCES world ( world_id ),
    objective_name VARCHAR ( 100 ),
    objective_desc VARCHAR ( 1024 ),
    difficulty INT,
    objective_url VARCHAR ( 256 ),
    supported_by VARCHAR ( 100 ),
    requires VARCHAR ( 100 ),
    objective_img VARCHAR ( 384 ),
    quest BYTEA,
    solution BYTEA
);

CREATE UNIQUE INDEX idx_objective_name
ON objective ( objective_name, world_id );

CREATE TABLE person (
    person_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES room ( room_id ),
    world_id INT REFERENCES world ( world_id),
    person_name VARCHAR ( 100 ),
    person_desc VARCHAR ( 1024 ),
    person_img VARCHAR ( 384 )
);

CREATE UNIQUE INDEX idx_person_name
ON person ( person_name, room_id );

CREATE TABLE junction (
    junction_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES room ( room_id ),
    world_id INT REFERENCES world ( world_id ),
    dest_id INT REFERENCES room ( room_id ),
    junction_desc VARCHAR ( 1024 )
);

CREATE UNIQUE INDEX idx_junction_dest
ON junction ( room_id, dest_id, world_id );

CREATE TABLE solution (
    solution_id SERIAL PRIMARY KEY,
    objective_id INT REFERENCES objective ( objective_id ),
    creator_id INT REFERENCES creator ( creator_id ),
    solution_text BYTEA
);

CREATE UNIQUE INDEX idx_solution_creator
ON solution ( objective_id, creator_id );

