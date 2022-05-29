CREATE TABLE creator (
    creator_id SERIAL PRIMARY KEY,
    creator_name VARCHAR ( 100 ) UNIQUE NOT NULL,
    creator_mail VARCHAR ( 100 ) UNIQUE NOT NULL,
    creator_desc VARCHAR ( 1024 ),
    creator_pass VARCHAR ( 256 ),
    creator_img VARCHAR ( 384 ),
    creator_role VARCHAR ( 20 ),
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE TABLE world (
    world_id SERIAL PRIMARY KEY,
    creator_id INT REFERENCES creator ( creator_id ),
    world_name VARCHAR ( 100 ) UNIQUE NOT NULL,
    world_desc VARCHAR ( 1024 ),
    world_url VARCHAR ( 256 ),
    world_img VARCHAR ( 384 ),
    visible INT default 0,
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE TABLE room (
    room_id SERIAL PRIMARY KEY,
    world_id INT REFERENCES world ( world_id ) ON DELETE CASCADE,
    room_name VARCHAR ( 100 ),
    room_desc VARCHAR ( 1024 ),
    room_img VARCHAR ( 384),
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE UNIQUE INDEX idx_room_name
ON room ( room_name, world_id );

CREATE TABLE item (
    item_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES room ( room_id ) ON DELETE CASCADE,
    world_id INT REFERENCES world ( world_id ) ON DELETE CASCADE,
    item_name VARCHAR ( 100 ),
    item_desc VARCHAR ( 1024 ),
    item_img VARCHAR ( 384 ),
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE UNIQUE INDEX idx_item_name
ON item ( item_name, world_id );

CREATE TABLE objective (
    objective_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES room ( room_id ) ON DELETE CASCADE,
    world_id INT REFERENCES world ( world_id ) ON DELETE CASCADE,
    objective_name VARCHAR ( 100 ),
    objective_title VARCHAR ( 100 ),
    objective_desc VARCHAR ( 1024 ),
    difficulty INT,
    objective_url VARCHAR ( 256 ),
    supported_by VARCHAR ( 100 ),
    requires VARCHAR ( 100 ),
    objective_img VARCHAR ( 384 ),
    quest BYTEA,
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE UNIQUE INDEX idx_objective_name
ON objective ( objective_name, world_id );

CREATE TABLE person (
    person_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES room ( room_id ) ON DELETE CASCADE,
    world_id INT REFERENCES world ( world_id) ON DELETE CASCADE,
    person_name VARCHAR ( 100 ),
    person_desc VARCHAR ( 1024 ),
    person_img VARCHAR ( 384 ),
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE UNIQUE INDEX idx_person_name
ON person ( person_name, room_id );

CREATE TABLE junction (
    junction_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES room ( room_id ) ON DELETE CASCADE,
    world_id INT REFERENCES world ( world_id ) ON DELETE CASCADE,
    dest_id INT REFERENCES room ( room_id ) ON DELETE CASCADE,
    junction_desc VARCHAR ( 1024 ),
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE UNIQUE INDEX idx_junction_dest
ON junction ( room_id, dest_id, world_id );

CREATE TABLE solution (
    solution_id SERIAL PRIMARY KEY,
    objective_id INT REFERENCES objective ( objective_id ),
    creator_id INT REFERENCES creator ( creator_id ) ON DELETE CASCADE,
    solution_text BYTEA,
    visible INT default 0,
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE UNIQUE INDEX idx_solution_creator
ON solution ( objective_id, creator_id );

CREATE TABLE invitation (
    invitation_id SERIAL PRIMARY KEY,
    invitation_code VARCHAR ( 20 ) UNIQUE NOT NULL,
    invitation_role VARCHAR ( 20 ) NOT NULL,
    invitation_forever INT default 0,
    invitation_taken INT default 0,
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE TABLE voting (
    voting_id SERIAL PRIMARY KEY,
    creator_id INT REFERENCES creator ( creator_id ) ON DELETE CASCADE,
    solution_id INT REFERENCES solution ( solution_id ) ON DELETE CASCADE,
    rating INT default 1,
    created timestamp default current_timestamp,
    modified timestamp default current_timestamp
);

CREATE UNIQUE INDEX idx_voting_creator
ON voting ( creator_id, solution_id );

CREATE OR REPLACE FUNCTION update_modified_column()   
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified = now();
    RETURN NEW;   
END;
$$ language 'plpgsql';

CREATE TRIGGER update_creator_modtime BEFORE UPDATE ON creator FOR EACH ROW EXECUTE PROCEDURE  update_modified_column();
CREATE TRIGGER update_world_modtime BEFORE UPDATE ON world FOR EACH ROW EXECUTE PROCEDURE  update_modified_column();
CREATE TRIGGER update_room_modtime BEFORE UPDATE ON room FOR EACH ROW EXECUTE PROCEDURE  update_modified_column();
CREATE TRIGGER update_item_modtime BEFORE UPDATE ON item FOR EACH ROW EXECUTE PROCEDURE  update_modified_column();
CREATE TRIGGER update_objective_modtime BEFORE UPDATE ON objective FOR EACH ROW EXECUTE PROCEDURE  update_modified_column();
CREATE TRIGGER update_person_modtime BEFORE UPDATE ON person FOR EACH ROW EXECUTE PROCEDURE  update_modified_column();
CREATE TRIGGER update_junction_modtime BEFORE UPDATE ON junction FOR EACH ROW EXECUTE PROCEDURE  update_modified_column();
CREATE TRIGGER update_solution_modtime BEFORE UPDATE ON solution FOR EACH ROW EXECUTE PROCEDURE  update_modified_column();

-- To be removed at a later stage
INSERT INTO invitation(invitation_code, invitation_role, invitation_forever) VALUES ('heureka', 'creator', 0);
INSERT INTO invitation(invitation_code, invitation_role, invitation_forever) VALUES ('sunshine', 'user', 1);