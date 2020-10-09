function [ChargingCapacity,DischargingCapacity]=ExtractCapacity(BatteryFileName,ChargingCapacityInput,DischargingCapacityInput)
% This script takes the cycler reports in .txt format and extracts the maximum accessed
% capacity on all charge steps and discharging steps and saves them into
% two different matricies
%% Reads the text file and outputs as a single cell array​
FullBatteryRead=textread(BatteryFileName,'%s');
%% Identifies the Charging Capacity and Discharging Capacity Index
ChargingCapacityIndex = find(strcmp([FullBatteryRead],'CCCV_Chg')); 
DischargingCapacityIndex = find(strcmp([FullBatteryRead],'CC_DChg'));
ChargingCapacityIndex = ChargingCapacityIndex + 2;
DischargingCapacityIndex = DischargingCapacityIndex + 2;
%% Identify the charging/discharging capacity and converts to a number
ChargingCapacityCycle=zeros(1,length(ChargingCapacityIndex));
DischargingCapacityCycle = zeros(1,length(DischargingCapacityIndex));
for i = 1:length(ChargingCapacityIndex)
    ChargingCapacityCycle(i) = str2num(FullBatteryRead{ChargingCapacityIndex(i)})/1000;
end
% dummy change. Discard me
for i = 1:length(DischargingCapacityIndex)
    DischargingCapacityCycle(i) = str2num(FullBatteryRead{DischargingCapacityIndex(i)})/1000;
end
%% Assigns the value to the output
ChargingCapacity = [ChargingCapacityInput;ChargingCapacityCycle];
DischargingCapacity = [DischargingCapacityInput;DischargingCapacityCycle];
end
