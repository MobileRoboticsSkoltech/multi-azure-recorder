#python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py \
#  --img-a    extracted-data/2022-03-24-14-13-47/1m/color/000016769422.png \
#  --img-b    extracted-data/2022-03-24-14-13-47/2s/color/000016769455.png \
#  --calib-a  calib_params/calib_1_000583592412.yaml \
#  --calib-b  calib_params/calib_2_000905794612.yaml \
#  --template calib_params/plane_sk_large.json \
#  --out-dir  calib_params/1-2_1

#python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py \
#  --img-a    extracted-data/2022-03-24-14-13-47/1m/color/000016769422.png \
#  --img-b    extracted-data/2022-03-24-14-13-47/9s/color/000017208533.png \
#  --calib-a  calib_params/calib_1_000583592412.yaml \
#  --calib-b  calib_params/calib_9_000489713912.yaml \
#  --template calib_params/plane_sk_large.json \
#  --out-dir  calib_params/1-9_1

#python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py \
#  --img-a    extracted-data/2022-03-24-14-13-47/2s/color/000016769455.png \
#  --img-b    extracted-data/2022-03-24-14-13-47/9s/color/000017208533.png \
#  --calib-a  calib_params/calib_2_000905794612.yaml \
#  --calib-b  calib_params/calib_9_000489713912.yaml \
#  --template calib_params/plane_sk_large.json \
#  --out-dir  calib_params/2-9_1

#python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py \
#  --img-a    extracted-data/2022-03-24-14-13-47/9s/color/000017208533.png \
#  --img-b    extracted-data/2022-03-24-14-13-47/2s/color/000016769455.png \
#  --calib-a  calib_params/calib_9_000489713912.yaml \
#  --calib-b  calib_params/calib_2_000905794612.yaml \
#  --template calib_params/plane_sk_large.json \
#  --out-dir  calib_params/9-2_1

####

#python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py \
#  --img-a    extracted-data/2022-03-24-14-13-47/1m/color/000055969433.png \
#  --img-b    extracted-data/2022-03-24-14-13-47/2s/color/000055769477.png \
#  --calib-a  calib_params/calib_1_000583592412.yaml \
#  --calib-b  calib_params/calib_2_000905794612.yaml \
#  --template calib_params/plane_sk_large.json \
#  --out-dir  calib_params/1-2_2

#python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py \
#  --img-a    extracted-data/2022-03-24-14-13-47/1m/color/000055969433.png \
#  --img-b    extracted-data/2022-03-24-14-13-47/9s/color/000056208533.png \
#  --calib-a  calib_params/calib_1_000583592412.yaml \
#  --calib-b  calib_params/calib_9_000489713912.yaml \
#  --template calib_params/plane_sk_large.json \
#  --out-dir  calib_params/1-9_2

#python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py \
#  --img-a    extracted-data/2022-03-24-14-13-47/2s/color/000055769477.png \
#  --img-b    extracted-data/2022-03-24-14-13-47/9s/color/000056208533.png \
#  --calib-a  calib_params/calib_2_000905794612.yaml \
#  --calib-b  calib_params/calib_9_000489713912.yaml \
#  --template calib_params/plane_sk_large.json \
#  --out-dir  calib_params/2-9_2

#python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py \
#  --img-a    extracted-data/2022-03-24-14-13-47/9s/color/000056208533.png \
#  --img-b    extracted-data/2022-03-24-14-13-47/2s/color/000055769477.png \
#  --calib-a  calib_params/calib_9_000489713912.yaml \
#  --calib-b  calib_params/calib_2_000905794612.yaml \
#  --template calib_params/plane_sk_large.json \
#  --out-dir  calib_params/9-2_2

tool="python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py"
out_path=$(echo "$1" | cut -d "/" -f2)
#date=$(date '+%Y-%m-%d-%H-%M-%S')

$tool --img-a $1 --img-b $2 --calib-a calib_params/calib_1_000583592412.yaml --calib-b  calib_params/calib_2_000905794612.yaml --template calib_params/plane_sk_large.json --out-dir calib_params/$out_path/1-2
$tool --img-a $1 --img-b $3 --calib-a calib_params/calib_1_000583592412.yaml --calib-b  calib_params/calib_9_000489713912.yaml --template calib_params/plane_sk_large.json --out-dir calib_params/$out_path/1-9
$tool --img-a $2 --img-b $3 --calib-a calib_params/calib_2_000905794612.yaml --calib-b  calib_params/calib_9_000489713912.yaml --template calib_params/plane_sk_large.json --out-dir calib_params/$out_path/2-9

#python3 ./Azure-Kinect-Sensor-SDK/examples/calibration_registration/register.py \
#  --img-a    extracted-data/2022-03-24-14-13-47/9s/color/000056208533.png \
#  --img-b    extracted-data/2022-03-24-14-13-47/2s/color/000055769477.png \
#  --calib-a  calib_params/calib_9_000489713912.yaml \
#  --calib-b  calib_params/calib_2_000905794612.yaml \
#  --template calib_params/plane_sk_large.json \
#  --out-dir  calib_params/kek
