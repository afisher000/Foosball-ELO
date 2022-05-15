% PBPL Foosball ELO Rating System
% Written by Andrew Fisher
% August 2019

% THIS FUNCTION COMPILES GAME STATS FOR EACH PLAYER AND OUTPUTS THE 
% RANKINGS FOR A GIVEN DAY, ALONG WITH CHANGES IN PAST WEEK

function Rankings(GL,R,fileID,numplayers,inputdate)

%% Create Player Info Table
for i=1:numplayers
    name=R.Properties.VariableNames{i};
    if i==1
        stats=PlayerInfo(GL,R,name);
    else
        stats=[stats;PlayerInfo(GL,R,name)];
    end
end
stats.Properties.RowNames=R.Properties.VariableNames(1:numplayers);


%% Create Ranking Table
% Prompt for day to output rankings
ordinal=datenum(inputdate,'mm/dd/yyyy');
pos=find(datenum(R.Date)==ordinal);

% Extract current and past ratings
Current=R{pos,1:numplayers};
WeekAgo=R{pos-7+1,1:numplayers};

% Keep track of how indices shift under sorting
[~,Iweek]=sort(WeekAgo,'descend');
[~,Icurrent]=sort(Current,'descend');

%% Calculate items for ranking table
[Rank,Name,Rating,RankChange,RatingChange]=deal(cell(numplayers,1));
for i=1:numplayers
    Rank(i)=num2cell(i);
    Name(i)=cellstr(R.Properties.VariableNames{Icurrent(i)});
    Rating(i)=num2cell(R{pos,Icurrent(i)});
    RatingChange(i)=num2cell(R{pos,Icurrent(i)}-R{pos-7,Icurrent(i)});
end
Rankings=table(Rank,Name,Rating,RatingChange);
Date={inputdate}; DateTable=table(Date);  % Include date of rankings

recycle on % Send to recycle bin instead of permanently deleting.
delete(fileID); % Delete (send to recycle bin).
writetable(stats,fileID,'Sheet','Stats');
writetable(Rankings,fileID,'Sheet','Rankings');
writetable(DateTable,fileID,'Sheet','Rankings','Range','E1:E2');

%% Create Condensed Ranking Table
% Only include players that have played num_games in the last num_days
% Search game log to find those that don't qualify
num_games=3;
num_days=28;
qualifyvec=zeros(1,numplayers);

for i=1:numplayers
    % Save name of player
    player=R.Properties.VariableNames{Icurrent(i)};
    % Restrict Log to last num_days
    GLTemp=GL(GL.OrdDate>=ordinal-num_days+1 & GL.OrdDate<=ordinal,:);
    % Restrict Log to player games
    GLTemp1=GLTemp(strcmp(player,GLTemp.WO),:);
    GLTemp2=GLTemp(strcmp(player,GLTemp.WD),:);
    GLTemp3=GLTemp(strcmp(player,GLTemp.LO),:);
    GLTemp4=GLTemp(strcmp(player,GLTemp.LD),:);
    
    % Populate QualifyVec
    if height([GLTemp1; GLTemp2; GLTemp3; GLTemp4])>= num_games
        qualifyvec(i)=1;
    end
end

% Calculate items for ranking table (Only include qualifying players)
[Rank,Name,Rating,RankChange,RatingChange]=deal(cell(numplayers,1));
for i=1:numplayers
    if qualifyvec(i)==1
        % j is index over qualified players
        j=sum(qualifyvec(1:i));
        Rank(j)=num2cell(j);
        Name(j)=cellstr(R.Properties.VariableNames{Icurrent(i)});
        Rating(j)=num2cell(R{pos,Icurrent(i)});
        RatingChange(j)=num2cell(R{pos,Icurrent(i)}-R{pos-7,Icurrent(i)});
    end
end

Rankings=table(Rank,Name,Rating,RatingChange);
Date={inputdate}; DateTable=table(Date);  % Include date of rankings

writetable(stats,fileID,'Sheet','Stats');
writetable(Rankings,fileID,'Sheet','CondensedRankings');
writetable(DateTable,fileID,'Sheet','CondensedRankings','Range','E1:E2');