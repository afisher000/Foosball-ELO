% PBPL Foosball ELO Rating System
% Written by Andrew Fisher
% August 2019

% THIS FUNCTION COMPUTES PLAYER RATINGS OVER TIME FROM GIVEN
% INITIAL RATINGS AND GAME DATA. NOTE THAT A DATE COLUMN IS APPENDED
% TO THE R (RATING) TABLE.

function output=Simulate(GL,R)
format='mm/dd/yyyy';
startday=datenum('7/29/2019',format); endday=round(now);

for i=startday:endday
    ii=i-startday+1;                    % Shifted index
    data=GL(GL.OrdDate==i,:);           % Game log for single day
    R{ii+1,:}=R{ii,:};                  % Populate next row
    
    % Loop through games from given day
    for j=1:height(data)
        P1=data{j,1}; P2=data{j,2}; P3=data{j,3}; P4=data{j,4}; Score=data{j,5};
        
        % Check for game type
        Winners='double';
        if strcmp(data{j,1}{1},data{j,2}{1})
            Winners='single';
        end
        Losers='double';
        if strcmp(data{j,3}{1},data{j,4}{1})
            Losers='single';
        end
            
            
        % Compute actual and expected "point win probability"
        RatingSpread=200;
        SW=10/(Score+10); SL=1-SW;
        WRating=(R{ii,P1}+R{ii,P2})/2; 
        LRating=(R{ii,P3}+R{ii,P4})/2;
        Diff=WRating-LRating;
        EW=1/(1+10^(-Diff/RatingSpread)); EL=1-EW;
        
        % Calculate adjustments with K=32 and update ratings
        K=32;
        Wadj=round(K*(SW-EW)); Ladj=round(K*(SL-EL));
        
        if strcmp(Winners,'double') && strcmp(Losers,'double')
            R{ii+1,P1}=R{ii+1,P1}+Wadj;
            R{ii+1,P2}=R{ii+1,P2}+Wadj;
            R{ii+1,P3}=R{ii+1,P3}+Ladj;
            R{ii+1,P4}=R{ii+1,P4}+Ladj;
        elseif strcmp(Winners,'double') && strcmp(Losers,'single')
            R{ii+1,P1}=R{ii+1,P1}+Wadj;
            R{ii+1,P2}=R{ii+1,P2}+Wadj;
            R{ii+1,P3}=R{ii+1,P3}+Ladj;
        elseif strcmp(Winners,'single') && strcmp(Losers,'double')
            R{ii+1,P1}=R{ii+1,P1}+Wadj;
            R{ii+1,P3}=R{ii+1,P3}+Ladj;
            R{ii+1,P4}=R{ii+1,P4}+Ladj;
        elseif strcmp(Winners,'single') && strcmp(Losers,'single')
            R{ii+1,P1}=R{ii+1,P1}+Wadj;
            R{ii+1,P3}=R{ii+1,P3}+Ladj;
        end
    end
    % Set VOID equal to 1000 again
    R{ii+1,end}=1000;
end

% Add dates for plotting
output=[R array2table(datetime(datestr(startday-1:1:endday,format)),'VariableNames',{'Date'})];
