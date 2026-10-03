/**
 * UI Constants and Preset Trip Scenarios
 */

export const PRESET_SCENARIOS = [
  {
    id: 'fmcsa-richmond-newark',
    title: 'FMCSA Guide Sample (Regional)',
    tag: 'Richmond → Newark (350 mi)',
    current: 'Richmond, VA',
    pickup: 'Richmond, VA',
    dropoff: 'Newark, NJ',
    cycleUsed: 12.0,
    desc: 'Matches John Doe Richmond to Newark sample from FMCSA guide.',
  },
  {
    id: 'short-haul',
    title: 'Short Haul (Midwest)',
    tag: 'Chicago → Milwaukee (92 mi)',
    current: 'Chicago, IL',
    pickup: 'Gary, IN',
    dropoff: 'Milwaukee, WI',
    cycleUsed: 5.0,
    desc: 'Quick day trip under standard shift limits.',
  },
  {
    id: 'medium-haul',
    title: 'Medium Haul (South)',
    tag: 'Dallas → Atlanta (785 mi)',
    current: 'Dallas, TX',
    pickup: 'Shreveport, LA',
    dropoff: 'Atlanta, GA',
    cycleUsed: 22.5,
    desc: 'Requires 30-min break and overnight 10h rest.',
  },
  {
    id: 'cross-country',
    title: 'Cross-Country Multi-Day',
    tag: 'Los Angeles → New York (2,800 mi)',
    current: 'Los Angeles, CA',
    pickup: 'Denver, CO',
    dropoff: 'New York, NY',
    cycleUsed: 18.0,
    desc: 'Long multi-day run with multiple 1,000-mi fuel stops and 10h rests.',
  },
  {
    id: 'high-cycle-restart',
    title: 'Max Cycle Edge Case (70h)',
    tag: 'Cycle = 70h (34h Restart)',
    current: 'Chicago, IL',
    pickup: 'Indianapolis, IN',
    dropoff: 'Columbus, OH',
    cycleUsed: 70.0,
    desc: 'Tests automatic 34-hour restart trigger before dispatch.',
  },
];

export const DEFAULT_LOG_HEADER = {
  driver_name: 'John E. Doe',
  driver_id: 'DRV-84920',
  carrier_name: 'US Freight Express LLC',
  main_office_address: '100 Logistics Blvd, Indianapolis, IN 46204',
  home_terminal_address: '450 Transport Way, Chicago, IL 60601',
  truck_tractor_num: 'T-804 (VIN: 1XKWD49X)',
  trailer_num: 'TR-5309 (IL Lic: 982-TRK)',
  co_driver: 'N/A (Solo Driver)',
  shipping_doc: 'BOL #9482104',
  shipper_commodity: 'General Freight / Commercial Goods',
};
