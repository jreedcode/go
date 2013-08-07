
CREATE TABLE stats 
  (num INTEGER PRIMARY KEY,
   lastVisit DATE,
   ipAddress TEXT,
   homeHits INT,
   goHits INT
  );

CREATE TABLE redirects
  (num INTEGER PRIMARY KEY,
   createDate DATE,
   source TEXT,
   destination TEXT,
   user TEXT,
   comment TEXT,
   goHits INT
  );
