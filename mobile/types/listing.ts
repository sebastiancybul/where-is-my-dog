export interface UserPreview {
	id: number;
	username: string;
	profile_photo: string | null;
}

export interface LocationPoint {
  type: 'Point';
  coordinates: [number, number]; // long, lat
}

export interface ListingLocation {
  id: number;
  added_by_user: number;
  listing: number;
  latitude: string;
  longitude: string;
  point: LocationPoint;
  address: string | null;
  location_type: 'exact' | 'approximate';
  is_primary: boolean;
  notes: string | null;
  accuracy_meters: number;
  created_at: string;
}

export interface ListingPhoto {
  id: number;
  cloudinary_url: string;
  thumbnail_url: string;
  order_index: number;
  uploaded_at: string;
}


export type ListingType = 'lost' | 'found'
type ListingStatus = 'active' | 'expired' | 'found' | 'returned'

export interface ListingItem {
  id: number;
  user: UserPreview;
  type: ListingType;
  status: ListingStatus;
  title: string;
  description: string;
  breed: string | null;
  size: string | null;
  color: string | null;
  gender: 'male' | 'female' | 'unknown';
  has_collar: boolean;
  collar_color: string | null;
  dog_name: string | null;
  age_estimate: string | null;
  special_marks: string | null;
  fostering_address: string | null;
  reward_offered: string | null;
  search_radius_km: number;
  photos: ListingPhoto[];
  photo_count: number;
  locations: ListingLocation[];
  primary_location: ListingLocation | null;
  public_conversation_id: number | null;
  public_conversation_is_closed: boolean | null;
  created_at: string;
  updated_at: string;
}

