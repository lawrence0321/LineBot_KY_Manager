window.addEventListener("load", () => {
    const liffID = '1656045539-NyWrBjZq';
    function initializeLiff(myLiffId) {
        liff
            .init({
                liffId: myLiffId
            })
            .then(() => {
                if (navigator.geolocation) {
                    // 支援GPS地理定位
                    navigator.geolocation.getCurrentPosition(showPosition, showError);
                }
                else {
                    alert("目前GPS無法定位");
                    liff.closeWindow();
                }

            })
            .catch((err) => {
                alert('啟動LIFF失敗。');
            });
    }

    function showPosition(position) {
        //alert(evt);
        sendLocationMessage(position.coords.latitude, position.coords.longitude);
    }


    function showError(error) {
        switch (error.code) {
            case error.PERMISSION_DENIED:
                alert("User denied the request for Geolocation.");
                break;
            case error.POSITION_UNAVAILABLE:
                alert("Location information is unavailable.");
                break;
            case error.TIMEOUT:
                alert("The request to get user location timed out.");
                break;
            case error.UNKNOWN_ERROR:
                alert("An unknown error occurred.");
                break;
        }
        liff.closeWindow();
    }

    function sendLocationMessage(latitude, longitude) {
        liff.sendMessages([
            {
                type: 'location',
                title: '打卡座標位置',
                address: '-',
                latitude: latitude,
                longitude: longitude
            }
        ]).then((res) => {
            window.alert(res.status);
            liff.closeWindow();
        })
            .catch(error => {

                window.alert(error);
                liff.closeWindow();
            });
    }

    //使用 LIFF_ID 初始化 LIFF 應用
    initializeLiff(liffID);
})

