# Pokémon dataset analysis

import pandas as pd
import numpy as np
from collections import defaultdict
from os.path import exists

# Functions
def parse_capture_rate(rate):
    """
    Deals with odd capture rates.
    """
    try:
        return int(rate)
    except ValueError:
        # For entries like '30 (Meteoric) 255(Core)', take first number
        return int(rate.split()[0])
    
def create_file():
    """
    Creates an input file for user to put Pokemon in.
    """
    pokemon_file = "pokemon_team.txt"
    if not exists(pokemon_file):
        with open("pokemon_team.txt", "w") as file:
            print("File has been created")
    else:
        pass
    print("Enter the names of SIX Pokemon in the file, on separate lines.")
    input()

class PokeData:
    def __init__(self):
        # Reordering columns as intended in the info file
        columns_order = [
    "name", "japanese_name", "pokedex_number", "percentage_male", "type1", 
    "type2", "classification", "height_m", "weight_kg", "capture_rate", 
    "base_egg_steps", "abilities", "experience_growth", "base_happiness", 
    "against_bug", "against_dark", "against_dragon", "against_electric", 
    "against_fairy", "against_fighting", "against_fire", "against_flying", 
    "against_ghost", "against_grass", "against_ground", "against_ice", 
    "against_normal", "against_poison", "against_psychic", "against_rock", 
    "against_steel", "against_water", "hp", "attack", "defense", "sp_attack", 
    "sp_defense", "speed", "generation", "is_legendary"
]       
        # Columns needed to make judgement
        self.key_columns = [
            "name", "type1", "capture_rate", "hp", "attack", "defense", 
            "sp_attack", "sp_defense", "speed", "score"
        ]

        # Fixing formatting of dataframe
        self.df = pd.read_csv(r'pokemon.csv')
        self.df = self.df[columns_order]
        self.df['capture_rate'] = self.df['capture_rate'].apply(parse_capture_rate)
        self.df['capture_rate'] = self.df['capture_rate'].astype(int)

        # Create input file
        create_file()

    def basic_optimal_team_build_plus(self):
        """
        Combines all algorithm options in the basic_optimal_team_build method.\n

        For info on how to let this method work, go to the basic_optimal_team_build method docstring.
        """
        # Combine scores into one and select top 15 Pokemon
        overall_scoring = defaultdict(int)
        best_pokemon_df = pd.DataFrame(columns=['name','score'])

        # Find cumulative best scorers 
        for i in range(1,6):
            df = self.basic_optimal_team_build(i)
            for j in range(len(df)):
                pokemon = df.iloc[j, :]
                overall_scoring[pokemon['name']] += pokemon['score']
        sorted_overall_scoring = sorted(overall_scoring.items(), reverse=True, key=lambda item: item[1])[:15]
        
        # Return dataframe form
        return pd.concat((best_pokemon_df, pd.DataFrame(sorted_overall_scoring, columns=['name','score'])), ignore_index=True)

    def basic_optimal_team_build(self, algorithm=1) -> pd.DataFrame:
        """
        Given a team of six Pokemon, display the best Pokemon choices to use
        against that team. \n

        Only compitable for Pokemon in generations 1 - 7. \n

        Use https://ptgigi.com/apps/pokemon/randomizer/ if you want to randomise Pokemon generation.\n

        Copy the team into the file made by the program.

        This team-building algorithm does not consider movesets, nor does it consider enemy Pokemon
        stats (expect type power).

        ALGORITHMS (enter numbers to choose algorithms):\n
        1 - Normal\n
        2 - Capture-Based (favours Pokemon that are easier to catch)\n
        3 - Aggressive (favours attack)\n
        4 - Tank (favours health and defense)\n
        5 - Fast (favours speed)\n
        """
        
        # Read file
        with open("pokemon_team.txt", "rt") as file:
            opposition = [pokemon.replace("\n", "") for pokemon in file.readlines()[:6]]

        # Create a score to influence best Pokemon choice
        self.df['score'] = np.zeros(len(self.df.index)).reshape(-1, 1).astype(int)

        # Find opposition Pokemon from dataframe
        oppostion_pokemon_df = self.df[self.df['name'].isin(opposition)].reset_index()

        # The dataframe where the best Pokemon are stored
        best_pokemon_df = pd.DataFrame()

        # Find effective types to then query into the dataframe again
        # Make a defualt dict to account for similar weaknesses in Pokemon
        effective_types_dict = defaultdict(int)
        
        against_types = [column for column in list(oppostion_pokemon_df.columns) if column.startswith('against_')]
        oppostion_pokemon_types_df = oppostion_pokemon_df[against_types]
    
        for i in range(len(oppostion_pokemon_types_df.index)):
            pokemon = oppostion_pokemon_types_df.iloc[i, :]
            weak_types = [column for column in against_types if pokemon[column] == pokemon.min()]
            for type in weak_types:
                effective_types_dict[type] += 1

        # Storing dict and finding all effective types
        effective_types = [type.split('_')[1] for type in list((dict(sorted(effective_types_dict.items(), reverse=True, key=lambda x: x[1]))).keys())]

        # Finding Pokemon that fit the effective type
        # Take into account priority
        for type in effective_types:
            effective_pokemon_df = self.df[self.df['type1'] == type][self.key_columns]

            # Readability purposes
            attack = effective_pokemon_df['attack']
            hp = effective_pokemon_df['hp']
            defense = effective_pokemon_df['defense']
            capture_rate = effective_pokemon_df['capture_rate']
            special_attack = effective_pokemon_df['sp_attack']
            special_defense = effective_pokemon_df['sp_defense']
            speed = effective_pokemon_df['speed']
            type_power = effective_types_dict[f'against_{type}']

            # Score formula
            # Normal
            if algorithm == 1:
                score_formula = type_power * (((attack + hp + defense + ((2 + type_power) * speed)) // 3 + capture_rate + max(1, (type_power)+1//2) * (special_attack + special_defense)))
            # Capture-based
            elif algorithm == 2:
                score_formula = (type_power * (5/510 * capture_rate)) * (((attack + hp + defense + ((2 + type_power) * speed)) // 3 + max(1, (type_power)+1//2) * (special_attack + special_defense)))
            # Aggressive
            elif algorithm == 3:
                score_formula = type_power * (((3 * attack - hp - defense)//5 + ((2 + type_power) * speed)) // 3 + capture_rate + max(1, (type_power)+1//2) * (3 * special_attack - special_defense))
            # Tank
            elif algorithm == 4:
                score_formula = type_power * (((5 * (3 * hp + 1.5 * defense) - attack + ((hp+defense)/10 + type_power) * speed/3)) // 3 + capture_rate + max(1, (type_power)+1//2) * (special_defense - special_attack))
            # Fast
            elif algorithm == 5:
                score_formula = type_power * (((attack + hp + defense)/5 + ((2 + type_power) * 5 * speed)) // 3 + capture_rate/1.5 + (max(1, (type_power)+1//2) * (special_attack + special_defense)/5))

            effective_pokemon_df['score'] = score_formula.astype(int)
            effective_pokemon_df = effective_pokemon_df.sort_values(by='score', ascending=False)
            best_pokemon_df = pd.concat((best_pokemon_df, effective_pokemon_df.head(4)))

        # Showing certain statistics based on chosen algorithm
        if algorithm == 1:
            return best_pokemon_df.sort_values(by='score', ascending=False)[['name', 'type1', 'score']].reset_index(drop=True).head(15)
        elif algorithm == 2:
            return best_pokemon_df.sort_values(by='score', ascending=False)[['name', 'type1', 'capture_rate', 'score']].reset_index(drop=True).head(15)
        elif algorithm == 3:
            return best_pokemon_df.sort_values(by='score', ascending=False)[['name', 'type1', 'attack', 'score']].reset_index(drop=True).head(15)
        elif algorithm == 4:
            return best_pokemon_df.sort_values(by='score', ascending=False)[['name', 'type1', 'hp', 'defense', 'score']].reset_index(drop=True).head(15)
        elif algorithm == 5:
            return best_pokemon_df.sort_values(by='score', ascending=False)[['name', 'type1', 'speed', 'score']].reset_index(drop=True).head(15)
