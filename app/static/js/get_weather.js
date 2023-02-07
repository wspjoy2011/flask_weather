const cityName = document.querySelector("#cityName");
const Temp = document.querySelector("#temp");
const main = document.querySelector("#main");
const description = document.querySelector("#description");
const image = document.querySelector("#image");

function getIP()  {
  const request = new XMLHttpRequest();
  request.open(
    "GET",
    'https://api64.ipify.org?format=json');
  request.send();
  request.onload = () => {
    if (request.status !== 404) {
      let data = JSON.parse(request.response);
      getLocation(data.ip)
    }
  }
};

function getLocation(ip) {
  const request = new XMLHttpRequest();
  request.open(
    "GET",
    `https://ipapi.co/${ip}/json/`);
  request.send();
  request.onload = () => {
    if (request.status !== 404) {
      let data = JSON.parse(request.response);
      weatherUpdate(data.city)
    }
  }
};


weatherUpdate = (city) => {
  const request = new XMLHttpRequest();
  request.open(
    "GET",
    `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=cad7ec124945dcfff04e457e76760d90`);

  request.send();
  request.onload = () => {
    if (request.status === 404) {
      alert("Place not found");
    } else {
      let data = JSON.parse(request.response);
      cityName.innerHTML = data.name;
      Temp.innerHTML = `${Math.round(data.main.temp - 273.15)}°C`;
      main.innerHTML = data.weather[0].main;
      description.innerHTML = data.weather[0].description;
      image.src = `https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png`;
    }
  };
};

getIP();

