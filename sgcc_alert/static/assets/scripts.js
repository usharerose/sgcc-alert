Apex.grid = {
  padding: {
    right: 0,
    left: 0
  }
}

Apex.dataLabels = {
  enabled: false
}

var colorPalette = ['#00D8B6','#008FFB',  '#FEB019', '#FF4560', '#775DD0']

var latestBalanceSparklineOption = {
  chart: {
    id: 'latestBalanceSparkline',
    group: 'sparklines',
    type: 'area',
    height: 160,
    sparkline: {
      enabled: true
    },
  },
  stroke: {
    curve: 'straight'
  },
  fill: {
    opacity: 1,
  },
  noData: {
    text: 'Loading...'
  },
  series: [],
  yaxis: {
    min: 0
  },
  xaxis: {
    type: 'datetime',
  },
  colors: ['#DCE6EC'],
  title: {
    text: '当前余额：Loading...',
    offsetX: 30,
    style: {
      fontSize: '24px',
      cssClass: 'apexcharts-yaxis-title'
    }
  },
  subtitle: {
    text: '更新日期：Loading...',
    offsetX: 30,
    style: {
      fontSize: '14px',
      cssClass: 'apexcharts-yaxis-title'
    }
  }
}

var monthlyUsageChartOption = {
  chart: {
    height: 340,
    type: 'area',
    zoom: {
      enabled: false
    },
  },
  stroke: {
    curve: 'straight'
  },
  colors: colorPalette,
  noData: {
    text: 'Loading...'
  },
  series: [],
  fill: {
    opacity: 1,
  },
  markers: {
    size: 0,
    style: 'hollow',
    hover: {
      opacity: 5,
    }
  },
  tooltip: {
    shared: true,
  },
  yaxis: [
    {
      title: {
        text: '用电量（KWh）',
      },
    },
    {
      opposite: true,
      title: {
        text: '电费（CNY）',
      },
    }
  ],
}

var latestBalanceSparklineChart = new ApexCharts(
  document.querySelector('#latestBalanceSparkline'),
  latestBalanceSparklineOption,
);
var monthlyUsageChart = new ApexCharts(
  document.querySelector('#monthlyUsageChartOption'),
  monthlyUsageChartOption,
);

latestBalanceSparklineChart.render();
monthlyUsageChart.render();

async function getResidentOptions() {
  const response = await axios.get('/api/v1.0/residents');
  const data = response.data;
  const residentSelector = document.getElementById('residentSelector');
  if (data.data?.length > 0) {
    residentSelector.innerHTML = '';
    data.data.forEach(resident => {
      const option = document.createElement('option');
      option.value = resident.resident_id;
      option.textContent = resident.resident_address;
      residentSelector.appendChild(option);
    });

    residentSelector.value = data.data[0].resident_id;
  }
}

function getRecentDateRange(days) {
  const today = new Date();
  const endDate = today.toISOString().split('T')[0];

  today.setDate(today.getDate() - days + 1);
  const startDate = today.toISOString().split('T')[0];

  return { startDate, endDate };
}

function initDateRangeFilter() {
  const { startDate, endDate } = getRecentDateRange(180);
  flatpickr("#dateRange", {
    mode: "range",
    dateFormat: "Y-m-d",
    defaultDate: [startDate, endDate],
    firstDayOfWeek: 1
  });
}

async function getLatestBalanceData(residentId) {
  const url = `/api/v1.0/residents/${residentId}/balances?order_by=date&order=desc&limit=1`;
  const response = await axios.get(url);
  const data = response.data;

  if (data.data.length > 0) {
    const latestData = data.data[0];
    return { value: latestData.balance, date: latestData.date };
  }
  return { value: null, date: null }
}

async function getRecentThirtyDaysUsageData(residentId) {
  const { startDate, endDate } = getRecentDateRange(30);
  const url = `/api/v1.0/residents/${residentId}/usages?start_date=${startDate}&end_date=${endDate}&granularity=daily`
  const response = await axios.get(url);
  const data = response.data;

  if (data.data.length > 0) {
    return data.data;
  }
  return [];
}

async function getMonthlyUsageData(residentId, startDate, endDate) {
  const url = `/api/v1.0/residents/${residentId}/usages?start_date=${startDate}&end_date=${endDate}&granularity=monthly`
  const response = await axios.get(url);
  const data = response.data;

  if (data.data.length > 0) {
    return data.data;
  }
  return [];
}

async function renderBalanceChart(residentId) {
  const latestBalanceData = await getLatestBalanceData(residentId);
  const { value, date } = latestBalanceData;
  const recentDailyUsageData = await getRecentThirtyDaysUsageData(residentId);

  latestBalanceSparklineChart.updateOptions({
    title: {
      text: `当前余额：CNY ${value}`,
    },
    subtitle: {
      text: `更新日期：${date}`,
    },
  });
  latestBalanceSparklineChart.updateSeries([{
    name: '电量（KWh）',
    data: recentDailyUsageData.map(item => ({
      x: item.date,
      y: item.elec_usage,
    })),
  }]);
}

async function renderMonthlyUsageChart(residentId, startDate, endDate) {
  const monthlyUsageData = await getMonthlyUsageData(residentId, startDate, endDate);

  monthlyUsageChart.updateSeries([
    {
      name: '用电量（KWh）',
      type: 'column',
      data: monthlyUsageData.map(item => ({
        x: item.date,
        y: item.elec_usage,
      })),
    },
    {
      name: '电费（CNY）',
      type: 'line',
      data: monthlyUsageData.map(item => ({
        x: item.date,
        y: item.elec_charge,
      })),
    },
  ]);
}

async function loadCharts() {
  const residentId = document.getElementById('residentSelector').value;
  const dateRange = document.getElementById('dateRange').value.split(' to ');
  const startDate = dateRange[0];
  const endDate = dateRange[1];

  if (residentId) {
    await renderBalanceChart(residentId);
    await renderMonthlyUsageChart(residentId, startDate, endDate);
  } else {
    alert('请填写所有筛选条件');
  }
}

function registerQueryEvent() {
  document.getElementById('queryButton').addEventListener('click', () => {
    loadCharts();
  });
}

async function init() {
  await getResidentOptions();
  initDateRangeFilter();
  registerQueryEvent();
  await loadCharts();
}

$(window).resize(function() {
  mobileDonut()
});

window.onload = async function () {
  await init();
};
