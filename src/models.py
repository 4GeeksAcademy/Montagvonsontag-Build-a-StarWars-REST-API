from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    #the below attributes are shown up in admin/User
    user_id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(50),nullable=False)
    
    #Relationships with other tables: 
    favourites: Mapped[list["Favourite"]] = relationship("Favourite", back_populates="user") #one to many relationship
    
    def serialize(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "favourites": [
                {
                    "id_character": fav.character.id_character,
                    "character_name": fav.character.character_name
                } for fav in self.favourites if fav.character
            ]
            # do not serialize the password, its a security breach
        }
    
class Character(db.Model):
    __tablename__ = "characters"
    id_character: Mapped[int] = mapped_column(primary_key=True)
    character_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
      
    # Relationships with other tables
    favourites: Mapped[list["Favourite"]] = relationship("Favourite", back_populates="character")

    def serialize(self):
        return {
            "id_character": self.id_character,
            "character_name": self.character_name,
            "favourite_character_of": [
                {
                    "user_id": fav.user.user_id,
                    "user_name": fav.user.user_name
                } for fav in self.favourites if fav.user
            ]    
        }     
    
#Association Table
class Favourite(db.Model):
    __tablename__ = "favourites"
        
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True,nullable=False)
    id_character: Mapped[int] = mapped_column(ForeignKey("characters.id_character"), primary_key=True, nullable=False)
    
    #Relationships with other tables
    user: Mapped["User"] = relationship("User",back_populates="favourites")
    character: Mapped["Character"] = relationship("Character", back_populates="favourites")

    def serialize(self):
        return {
            
            "user": {
                "user_id": self.user_id               
            } if self.user else None,    
            "character": {
                "id_character": self.id_character                
            } if self.character else None,           
        }    
    
    