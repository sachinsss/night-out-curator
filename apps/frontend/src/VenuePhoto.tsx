import { useState } from "react";
import { Utensils, ImageOff, ChevronLeft, ChevronRight } from "lucide-react";
import type { PlacePresentation } from "@night-out/contracts";
import { placePhotoUrl } from "./presentation-api";
import { Button } from "./components/ui/button";

type Photo = PlacePresentation["photos"][number];
function PhotoImage({
  photo,
  name,
  large = false,
}: {
  photo: Photo | undefined;
  name: string;
  large?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  return photo && !failed ? (
    <img
      src={placePhotoUrl(photo.name, large ? 1280 : 640)}
      alt={`${name} venue`}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  ) : (
    <div className="venue-photo-placeholder">
      <span>{failed ? <ImageOff /> : <Utensils />}</span>
      <small>{failed ? "Photo unavailable" : "No photo available"}</small>
      {failed && (
        <button type="button" onClick={() => setFailed(false)}>
          Retry photo
        </button>
      )}
    </div>
  );
}
export function VenuePhoto({
  photos = [],
  name,
  loading = false,
  gallery = false,
}: {
  photos?: Photo[] | undefined;
  name: string;
  loading?: boolean;
  gallery?: boolean;
}) {
  const [index, setIndex] = useState(0);
  const photo = photos[index];
  return (
    <figure
      className={`venue-photo ${gallery ? "venue-gallery" : ""} ${loading ? "photo-loading" : ""}`}
    >
      {loading ? (
        <div className="photo-skeleton" aria-label="Loading venue photo" />
      ) : (
        <PhotoImage key={photo?.name ?? "empty"} photo={photo} name={name} large={gallery} />
      )}
      {gallery && photos.length > 1 && (
        <div className="gallery-controls">
          <Button
            type="button"
            variant="secondary"
            size="icon-sm"
            aria-label="Previous photo"
            onClick={() => setIndex((value) => (value + photos.length - 1) % photos.length)}
          >
            <ChevronLeft />
          </Button>
          <span>
            {index + 1} / {photos.length}
          </span>
          <Button
            type="button"
            variant="secondary"
            size="icon-sm"
            aria-label="Next photo"
            onClick={() => setIndex((value) => (value + 1) % photos.length)}
          >
            <ChevronRight />
          </Button>
        </div>
      )}
      {photo && (
        <figcaption>
          {photo.authors.length
            ? photo.authors.map((author, i) => (
                <span key={`${author.name}-${i}`}>
                  {i > 0 ? ", " : ""}
                  {author.uri ? (
                    <a href={author.uri} target="_blank" rel="noreferrer">
                      {author.name}
                    </a>
                  ) : (
                    author.name
                  )}
                </span>
              ))
            : "Google Maps"}
          {photo.sourceUri && (
            <a
              href={photo.sourceUri}
              target="_blank"
              rel="noreferrer"
              aria-label={`View source photo for ${name}`}
            >
              {" "}
              · Source
            </a>
          )}
        </figcaption>
      )}
    </figure>
  );
}
