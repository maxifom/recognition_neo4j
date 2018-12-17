# USAGE
# python recognize_faces_video.py --encodings encodings.pickle
# python recognize_faces_video.py --encodings encodings.pickle --output output/jurassic_park_trailer_output.avi --display 0

import os
from PIL import Image
# import the necessary packages
from imutils.video import VideoStream
from _neo4j import *
# from main import event
from event import event
def StartRecognition(display=1, method='hog'):
    DeleteGraph()
    vs = VideoStream(src=0).start()
    writer = None
    # time.sleep(2.0)

    # loop over frames from the video file stream
    faces = GetAllFacesFromGraph()
    while True:
        if event.is_set():
            event.clear()
            faces = GetAllFacesFromGraph()
            print("Updating faces from graph")

        # grab the frame from the threaded video stream
        frame = vs.read()

        # convert the input frame from BGR to RGB then resize it to have
        # a width of 750px (to speedup processing)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(rgb)
        # rgb = imutils.resize(frame, width=750)

        r = frame.shape[1] / float(rgb.shape[1])

        # detect the (x, y)-coordinates of the bounding boxes
        # corresponding to each face in the input frame, then compute
        # the facial embeddings for each face
        boxes = face_recognition.face_locations(rgb,
                                                model=method)
        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []

        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(faces['faces'],
                                                     encoding)
            name = "Unknown"

            # check to see if we have found a match
            if True in matches:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}

                # loop over the matched indexes and maintain a count for
                # each recognized face face
                for i in matchedIdxs:
                    name = faces["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)
            if name == 'Unknown':
                name = AddUnknownToGraph(encoding.tolist())
                faces = GetAllFacesFromGraph()
            # update the list of names
            names.append(name)
        # loop over the recognized faces
        for ((top, right, bottom, left), name) in zip(boxes, names):
            # rescale the face coordinates
            top = int(top * r)
            right = int(right * r)
            bottom = int(bottom * r)
            left = int(left * r)

            # Save unknown face to disk

            numbers = 5
            IE = ImagesExists(name, numbers)
            if 'Unknown' in name and IE > 0:
                face_image = image_pil.crop((left - 35, top - 35, right + 35, bottom + 35))
                face_image.save('./images/' + str(name) + '_' + str(IE) + '.jpg')

            # draw the predicted face name on the image
            cv2.rectangle(frame, (left, top), (right, bottom),
                          (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, (0, 255, 0), 2)

        # check to see if we are supposed to display the output frame to
        # the screen
        if display > 0:
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break
        AddWalksWhenToNames(names)
        AddWalksWithRelathionshipInIntervalForNames(names)

    # do a bit of cleanup
    cv2.destroyAllWindows()
    vs.stop()


def ImagesExists(name, numbers):
    # if os.path.isfile('./images/' + str(name)+'.exist'):
    #     return 0
    for number in range(0, numbers + 1):
        if os.path.isfile('./images/' + str(name) + '_' + str(number) + '.jpg'):
            return number - 1
    return numbers


if __name__ == '__main__':
    # DeleteGraph()
    # event = threading.Event()
    # thread_recognition = threading.Thread(target=StartRecognition)
    # thread_server = threading.Thread(target=StartServer)
    # thread_server.start()
    # thread_recognition.start()
    # StartServer()
    StartRecognition()