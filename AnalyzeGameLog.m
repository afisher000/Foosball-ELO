% PBPL Foosball ELO Rating System
% Written by Andrew Fisher
% August 2019

% THIS FUNCTION ALLOWS THE USER TO ANALYZE THE DATA STORED IN THE FOOSBALL
% GAME LOG BY SPECIFYING SPECIFIC TEAMS AND DATES. FOR GAMETYPE='DOUBLES',
% THE RESULTS WILL INCLUDE A BREAKDOWN OF EACH POSSIBLE MATCHUP FOR THE TWO
% TEAMS. THE KEYWORD 'ANY' STANDS FOR 'ANY PLAYER' AND ALLOWS THE USER TO
% FIND ALL THE GAMES WHERE TWO INDIVIDUALS PLAYED AGAINST EACH OTHER IN
% DOUBLES GAMES. FINALLY, SPECIFIC PLAYER RESULTS ARE GIVEN FOR THE DATE
% RANGE. FOR EXAMPLE, YOU COULD SEE WHO PLAYED THE BEST IN A GIVEN MONTH.

function AnalyzeGameLog()
close all;
clear vars;

%% Read In Logs
[GL,R,numplayers,error]=ReadCheckLog();
if error==1
    return;
end

%% User Search Input
format='mm/dd/yyyy';

% Enter date range manually (First logged date is '7/29/2019'). Note that
% the search will include games played on the start and end dates.
startdate=datenum('7/29/2019',format); 
enddate=datenum('03/02/2020',format);


% Enter player names in a cell matrix ('ANY' is possible option for P2 and P4 only)
P={'victor','victor','ANY','ANY'};
Pnames={P{1},P{2},P{3},P{4}};

% Enter game type ('doubles' or 'singles')
% If gametype='singles', the code will lookup matchups between P(1) and
% P(3)
gametype='singles';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Results will be exported to the excel sheet 'ResultsByMatchup.xlsx' %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%



%% Retrieve and Output Data

% Deal with 'any' input by replacing 'any' with array of all player names
for i=1:length(P)
    if strcmp(P{i},'ANY')
        P{i}=R.Properties.VariableNames;
    end
end

if strcmp(gametype,'doubles');
    % Redefine GL to only cover specified date range
    GL=GL(GL.OrdDate>=startdate & GL.OrdDate<=enddate,:);
    GLbyDATE=GL;
    % Remove Singles Games
    GL=GL(not(strcmp(GL.WO,GL.WD)) & not(strcmp(GL.LO,GL.LD)),:);
    % Create excel sheet with all matchup permutations
    DoublesResults(GL,P,Pnames);
    
elseif strcmp(gametype,'singles');
    % Redefine GL to only cover specified date range
    GL=GL(GL.OrdDate>=startdate & GL.OrdDate<=enddate,:);
    GLbyDATE=GL;
    % Only Keep Singles Games
    GL=GL(strcmp(GL.WO,GL.WD) & strcmp(GL.LO,GL.LD),:);
    
    SinglesResults(GL,P,Pnames)
    
else
    fprintf('Error, variable stored in gametype is not valid.')
    return;
end

%% Create Player Info Table
for i=1:numplayers
    name=R.Properties.VariableNames{i};
    if i==1
        stats=PlayerInfo(GLbyDATE,R,name);
    else
    stats=[stats;PlayerInfo(GLbyDATE,R,name)];
    end
end



fileID='ResultsByMatchup.xlsx';
stats.Properties.RowNames=R.Properties.VariableNames(1:numplayers);
writetable(stats,fileID,'Sheet','Individual Player Stats');

end
  
    
%% Local Functions

function DoublesResults(GL,P,Pnames)
    % Returns stats and gamelog for different matchups for
    % gametype='doubles'
    PermVec={[1,2,3,4],[1,2,4,3],[2,1,3,4],[2,1,4,3]};
    
    % If 'ANY' is entered for both players on a team, adjust PermVec so
    % that games aren't double counted.
    if strcmp(Pnames{3},'ANY') && strcmp(Pnames{4},'ANY')
        if strcmp(Pnames{1},'ANY') && strcmp(Pnames{2},'ANY')
            PermVec={[1,2,3,4]};
        else
            PermVec={[1,2,3,4],[2,1,3,4]};
        end
    elseif strcmp(Pnames{1},'ANY') && strcmp(Pnames{2},'ANY')
            PermVec={[1,2,3,4],[1,2,4,3]};
    end

    % Loop over possible team matchups
    for i=1:length(PermVec)
        [S,L]=GetGameStats(GL,PermVec{i},P,Pnames);
        if i==1
            stats=S; gamelog=L;
        else
            stats=[stats;S]; gamelog=[gamelog;L]; 
        end
    end

    % Compute overall team matchup stats
    Games=sum(table2array(stats(:,5)));
    Wins=sum(table2array(stats(:,6)));
    Losses=sum(table2array(stats(:,7)));
    WinPct=round(Wins/Games,2);
    PointsFor=sum(table2array(stats(:,9)));
    PointsAgainst=sum(table2array(stats(:,10)));
    PointsDiff=PointsFor-PointsAgainst;
    NormPointsDiff=round(PointsDiff/Games,2);
    Offense1={''}; Defense1={''}; Offense2={''}; Defense2={'Totals:'};
    
    S=table(Offense1,Defense1,Offense2,Defense2,Games,Wins,Losses,WinPct,PointsFor,PointsAgainst,PointsDiff,NormPointsDiff);
    stats=[stats;S];
    
    fileID='AnalyzeGameLogResults.xlsx';
    recycle on % Send to recycle bin instead of permanently deleting.
    delete(fileID); % Delete (send to recycle bin).
    writetable(stats,fileID,'Sheet','Stats by Team Matchup');
    writetable(gamelog,fileID,'Sheet','GameLog');
end

function SinglesResults(GL,P,Pnames)
    % Returns stats and gamelog for gametype='singles'
    [S,L]=GetGameStats(GL,[1,1,3,3],P,Pnames);
    stats=S; gamelog=L;
   
    fileID='AnalyzeGameLogResults.xlsx';
    writetable(stats,fileID,'Sheet','Stats by Singles Matchup');
    writetable(gamelog,fileID,'Sheet','GameLog');
end


function [stats, data]=GetGameStats(GL,permvec,P,Pnames)

Offense1=Pnames(permvec(1));
Defense1=Pnames(permvec(2));
Offense2=Pnames(permvec(3));
Defense2=Pnames(permvec(4));

T={P{permvec(1)},P{permvec(2)},P{permvec(3)},P{permvec(4)}};

% Find games for specific matchup
WinLog=GL(ismember(GL.WO,T{1}) & ismember(GL.WD,T{2}) & ismember(GL.LO,T{3}) & ismember(GL.LD,T{4}),:);
LossLog=GL(ismember(GL.WO,T{3}) & ismember(GL.WD,T{4}) & ismember(GL.LO,T{1}) & ismember(GL.LD,T{2}),:);

% Compute statistics
Wins=height(WinLog);
Losses=height(LossLog);
Games=Wins+Losses;
WinPct=round(Wins/Games,2);
PointsFor=10*Wins+sum(table2array(LossLog(:,5)));
PointsAgainst=10*Losses+sum(table2array(WinLog(:,5)));
PointsDiff=PointsFor-PointsAgainst;
NormPointsDiff=round(PointsDiff/Games,2);

% Return results as tables
stats=table(Offense1,Defense1,Offense2,Defense2,Games,Wins,Losses,WinPct,PointsFor,PointsAgainst,PointsDiff,NormPointsDiff);
data=[WinLog; LossLog];

end