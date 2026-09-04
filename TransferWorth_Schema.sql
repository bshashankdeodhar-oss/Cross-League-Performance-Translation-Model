-- ============================================================
-- PROJECT TITLE: Transfer Worth
-- STUDENT NAME : Shashank Deodhar Bantupalli
-- REG NO       : 24BRS1297
-- INSTITUTION  : VIT Chennai
-- ============================================================

CREATE TABLE League (
    league_id INT PRIMARY KEY AUTO_INCREMENT,
    league_name VARCHAR(255) NOT NULL UNIQUE,
    lsc_coefficient FLOAT NOT NULL DEFAULT 1.0,
    country VARCHAR(100)
);

CREATE TABLE Team (
    team_id INT PRIMARY KEY AUTO_INCREMENT,
    team_name VARCHAR(255) NOT NULL,
    league_id INT NOT NULL,
    team_strength_ratio FLOAT DEFAULT 1.0,
    FOREIGN KEY (league_id) REFERENCES League(league_id) ON DELETE CASCADE
);

CREATE TABLE User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer'
);

CREATE TABLE Player (
    player_id INT PRIMARY KEY AUTO_INCREMENT,
    player_name VARCHAR(255) NOT NULL,
    position VARCHAR(50),
    position_primary VARCHAR(50),
    age FLOAT,
    team_id INT,
    league_id INT NOT NULL,
    FOREIGN KEY (team_id) REFERENCES Team(team_id) ON DELETE SET NULL,
    FOREIGN KEY (league_id) REFERENCES League(league_id) ON DELETE CASCADE
);

CREATE TABLE PlayerStats (
    stats_id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL UNIQUE,
    minutes FLOAT,
    goals FLOAT,
    assists FLOAT,
    xg FLOAT,
    xag FLOAT,
    goals_p90 FLOAT,
    assists_p90 FLOAT,
    xg_p90 FLOAT,
    xag_p90 FLOAT,
    prog_passes_p90 FLOAT,
    prog_carries_p90 FLOAT,
    key_passes_p90 FLOAT,
    pass_completion_pct FLOAT,
    lsc_adj_goals_p90 FLOAT,
    lsc_adj_xg_p90 FLOAT,
    FOREIGN KEY (player_id) REFERENCES Player(player_id) ON DELETE CASCADE
);

CREATE TABLE PlayerStyleProfile (
    profile_id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL UNIQUE,
    age_curve_score FLOAT,
    play_style_progressive FLOAT,
    play_style_direct_carry FLOAT,
    play_style_defensive FLOAT,
    poss_adj_touches_p90 FLOAT,
    FOREIGN KEY (player_id) REFERENCES Player(player_id) ON DELETE CASCADE
);

CREATE TABLE TransferPrediction (
    prediction_id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL,
    user_id INT,
    source_league_id INT NOT NULL,
    target_league_id INT NOT NULL,
    projected_goals_p90 FLOAT,
    projected_assists_p90 FLOAT,
    projected_xg_p90 FLOAT,
    ci_low_goals FLOAT,
    ci_high_goals FLOAT,
    adaptation_score_pct FLOAT,
    risk_score_pct FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES Player(player_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE SET NULL,
    FOREIGN KEY (source_league_id) REFERENCES League(league_id),
    FOREIGN KEY (target_league_id) REFERENCES League(league_id)
);

CREATE TABLE ScenarioSimulation (
    simulation_id INT PRIMARY KEY AUTO_INCREMENT,
    prediction_id INT NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_val_simulated FLOAT NOT NULL,
    simulated_target_val FLOAT NOT NULL,
    FOREIGN KEY (prediction_id) REFERENCES TransferPrediction(prediction_id) ON DELETE CASCADE
);
