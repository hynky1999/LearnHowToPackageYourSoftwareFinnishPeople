

const url = 'http://127.0.0.1:8000/';
const defaultEmbodySource = '/static/img/dummy_600.png';

$(document).ready(function() {

    // Init draw variables
    /*
    OO-style coordinates:
    var paint;
    var point = {
        x: null,
        y: null,
        r: 13
    }
    var points = new Array()
    */
    var clickX = new Array();
    var clickY = new Array();
    var clickRadius = new Array();
    var clickDrag = new Array();
    var paint;
    var width = 0;
    var height = 0;
    var drawRadius=13
    var default_embody=false
    var points = []
    var imageId = null;

    try {
        var canvas = $("#embody-canvas")
        var canvasInfo = $(".canvas-info")
        var context = document.getElementById("embody-canvas").getContext("2d");

        //var oldimg = document.getElementById("baseImage");
        var img = $('.embody-image.selected-embody')[0]

        $(img).on('load', function() {
            drawImage()
        })

    } catch (e) {
        console.log(e)
        if (e instanceof TypeError) {
            return
        }
    }

    function drawImage() {

        newImage = new Image();
        newImage.src =  img.src

        newImage.onload = function() {
            imageId = img.id
            width = newImage.width;
            height = newImage.height;
            context.canvas.height = height
            context.canvas.width = width
            context.drawImage(newImage, 0, 0);
            $(img).hide()
        }
    }

    // Click handlers
    canvas.mousedown(function(e){
        var mouseX = e.pageX - this.offsetLeft;
        var mouseY = e.pageY - this.offsetTop;
        paint = true;

        if (pointInsideBaseImage([mouseX, mouseY])) {
            addClick(mouseX, mouseY);
            redraw();
        }
    });

    canvas.mousemove(function(e){
        // TODO: if mousedown -> can draw outside of image
        var mouseX = e.pageX - this.offsetLeft;
        var mouseY = e.pageY - this.offsetTop;

        if (paint && pointInsideBaseImage([mouseX, mouseY])){
            addClick(mouseX, mouseY, true);
            redraw();
        }
    });

    canvas.mouseup(function(e){
        paint = false;
    });

    canvas.mouseleave(function(e){
        paint = false;
    });


    // TODO: changing drawradius doesnt affect to the saved datapoints !!!
    // Bigger brush should make more datapoints compared to smaller ones.
    // add brush size to click arry -> {x:[...], y:[...], size:[...]} ?? 
    
    $("#embody-canvas").bind('DOMMouseScroll', changeBrushSize)
    // DOMMouseScroll is only for firefox
    //$(".canvas-container").bind('wheel', changeBrushSize)
    
    function changeBrushSize(event) {
        event.preventDefault()

        // Change brush size
        if (event.originalEvent.detail >= 0){
            if (drawRadius >= 13) {
                drawRadius -= 5; 
            }
        } else {
            if (drawRadius <= 13) {
                drawRadius += 5; 
            }
        }

        // Show brush size to user
        if (drawRadius == 8) {
            canvasInfo.html("small brush")
        } else if (drawRadius == 13) {
            canvasInfo.html("normal brush")
        } else if (drawRadius == 18) {
            canvasInfo.html("large brush")
        }
    }

    $(".clear-button").on('click', function() {
        clearCanvas()
    })

    $(".next-page").click(function() {
        saveData()
    })


    function saveData() {

        points.push({
            id: imageId,
            x: clickX,
            y: clickY,
            r: clickRadius,
            width: width,
            height: height
        })

        clickX = []
        clickY = []
        clickRadius = []

        if ($(img).hasClass('last-embody')) {
            // Send data to db
            try {
                console.log(points)
                points = JSON.stringify(points)
                $("#canvas-data").val(points);
                $("#canvas-form").submit();
            } catch(e) {
                console.log(e)
            }

        } else {
            // Show next picture
            img = img.nextElementSibling

            try {
                drawImage()
            } catch(e) {
                console.log(e)
            }
        }
    }

    // Draw methods
    function addClick(x, y, dragging=false) {
        clickX.push(x);
        clickY.push(y);
        clickRadius.push(drawRadius);
        clickDrag.push(dragging);
    }

    function drawPoint(x, y, radius) {
        context.beginPath();
        context.arc(x, y, radius, 0, 2 * Math.PI, false);
        context.fill()
    }

    function isWhite(color) {
        return (color === 255) ? true : false;
    }

    // Method for checking if cursor is inside human body before creating brush stroke
    function pointInsideBaseImage(point) {

        if (default_embody) {
            var imageData = context.getImageData(point[0], point[1],1,1)

            startR = imageData.data[0];
            startG = imageData.data[1];
            startB = imageData.data[2];

            return (isWhite(startB) && isWhite(startG) && isWhite(startR)) ? false : true;
        } else {
            return true
        }
    }

    function redraw() {
        /* 
        Check:
        https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/globalCompositeOperation

        TODO: It's possible to use only one mask image propably
        */
        //context.globalCompositeOperation='destination-over' // 
        //context.clearRect(0, 0, context.canvas.width, context.canvas.height); // Clears the canvas

        lastX = clickX[clickX.length - 1]
        lastY = clickY[clickY.length - 1]

        // Opacity (there was 0.2 opacity in the old version):
        context.globalAlpha = 0.15
        
        // Gradient:
        var gradient = context.createRadialGradient(lastX, lastY, 1, lastX, lastY, drawRadius);


        gradient.addColorStop(0, "rgba(255,0,0,1)");
        gradient.addColorStop(1, "rgba(255,0,0,0.1)");


        context.fillStyle = gradient

        // Draw circle with gradient
        drawPoint(lastX, lastY, drawRadius)


        // Draw mask on default image
        
        if (img.getAttribute('src') === defaultEmbodySource) {
            drawMaskToBaseImage()
        }

    }

    function drawMaskToBaseImage() {
        var img = document.getElementById("baseImageMask");
        context.globalAlpha = 1
        context.drawImage(img, 0, 0);
    }

    function drawBaseImage() {
        var width = img.width;
        var height = img.height;

        context.canvas.height = height
        context.canvas.width = width

        context.drawImage(img, 0, 0);
        $(img).hide()
    }

    function clearCanvas() {
        context.clearRect(0, 0, context.canvas.width, context.canvas.height);
        drawBaseImage()

        // Remove saved coordinates
        clickX = []
        clickY = []
        clickDrag = []
    }



    drawImage()
            
});