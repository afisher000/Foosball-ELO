function output=PlayerInfo(GL,R,input)
% Outputs statistics for given player
% input can be player name or index in R table
if isa(input,'double')
    Name=R.Properties.VariableNames{input};
elseif isa(input,'char')
    Name=input;
else
    fprintf('Input is not index or name...');
    return;
end

% Extract column information
wovec=strcmp(GL{:,{'WO'}},Name);
wdvec=strcmp(GL{:,{'WD'}},Name);
lovec=strcmp(GL{:,{'LO'}},Name);
ldvec=strcmp(GL{:,{'LD'}},Name);
scorevec=GL{:,{'Score'}};

% Calculate stats
OffWins=nnz(wovec);
DefWins=nnz(wdvec);
OffLosses=nnz(lovec);
DefLosses=nnz(ldvec);
Wins=OffWins+DefWins;
Losses=OffLosses+DefLosses;
Games=Wins+Losses;

WinPct=round(Wins/Games,2);
OffWinPct=round(OffWins/(OffWins+OffLosses),2);
DefWinPct=round(DefWins/(DefWins+DefLosses),2);

PointsFor=sum(wovec*10+wdvec*10+lovec.*scorevec+ldvec.*scorevec);
PointsAgainst=sum(wovec.*scorevec+wdvec.*scorevec+ldvec*10+lovec*10);
PointsDiff=PointsFor-PointsAgainst;
NormPointsDiff=round(PointsDiff/Games,2);
Names={Name};

% Output Table
output=table(Names,Games,Wins,Losses,WinPct,OffWinPct, DefWinPct,OffWins,DefWins,OffLosses,DefLosses,PointsFor,PointsAgainst,PointsDiff,NormPointsDiff);