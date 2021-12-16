function PlotRatings(R,numplayers)
%% Plot Ratings vs. Time
figure(1); hold on; title('ELO Ratings');
for i=1:numplayers
    plot(R{:,numplayers+1},R{:,i})
end
legend(R.Properties.VariableNames(1:numplayers));
hold off;