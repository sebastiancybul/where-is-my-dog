import { View, Text, ScrollView, Pressable, TextInput, Switch } from 'react-native'
import React, { useEffect, useState } from 'react'
import { FontAwesome5, Ionicons, MaterialCommunityIcons } from "@expo/vector-icons"
import BreedPicker from "@/components/BreedPicker"
import { COLOR_OPTIONS } from "@/constants/dogOptions"
import { ListingCreate } from "@/types/listingForm"

type Props = {
  onChange: (data: Partial<ListingCreate>) => void;
  initialData?: Partial<ListingCreate>;
}

const DogDetailsStep = ({onChange, initialData}: Props) => {
  const [breedActive, setBreedActive] = useState<boolean>(!!initialData?.breed);
  const [breed, setBreed] = useState<string>(initialData?.breed ?? "");
  const [sizeActive, setSizeActive] = useState<boolean>(!!initialData?.size);
  const [size, setSize] = useState<'small' | 'medium' | 'large' >(initialData?.size ?? "small");
  const [colorActive, setColorActive] = useState<boolean>(true);
  const [colors, setColors] = useState<string[]>(initialData?.color ? initialData.color.split(',').filter(Boolean) : []);
  const [genderActive, setGenderActive] = useState<boolean>(!!initialData?.gender);
  const [gender, setGender] = useState<'male' | 'female' | 'unknown'>(initialData?.gender ?? 'unknown');
  const [extrasActive, setExtrasActive] = useState<boolean>(!!(initialData?.dog_name || initialData?.age_estimate || initialData?.special_marks || initialData?.has_collar));
  const [dogName, setDogName] = useState<string>(initialData?.dog_name ?? "");
  const [age, setAge] = useState<string>(initialData?.age_estimate ?? "");
  const [specialMarks, setSpecialMarks] = useState<string>(initialData?.special_marks ?? "");
  //const [microchip, setMicrochip] = useState<boolean>(false);
  const [hasCollar, setHasCollar] = useState<boolean>(initialData?.has_collar ?? false);
  const [collarColor, setCollarColor] = useState<string>(initialData?.collar_color ?? "");

  const toggleColor = (val: string) =>
    setColors(prev => prev.includes(val) ? prev.filter(v => v !== val) : [...prev, val]);

  useEffect(() => {
    const color = colors.join(',');
    onChange({breed, size, color: color, gender, has_collar: hasCollar, collar_color: collarColor, dog_name: dogName, age_estimate: age, special_marks: specialMarks, })

  },[breed, size, colors, gender, dogName, age, specialMarks, hasCollar, collarColor])

  return (
    <ScrollView
      contentContainerStyle={{ paddingBottom: 400 }}
    >
      <View className="bg-white px-4 pt-4 pb-2 mb-4 flex w-full rounded-xl">
        <Pressable
            onPress={() => setBreedActive(!breedActive)}
            className="active:opacity-80"
          >
          <View className="flex-row items-center relative mb-4">
            <FontAwesome5 name="dog" size={16} color="brown" className="bg-yellow-100 px-2 py-2 rounded-xl" />
            <Text className="ml-2 font-semibold text-gray-800">Breed</Text>
            {breed.length > 0 && (
              <Text className="ml-2 text-sm text-blue-600 font-medium">{breed}</Text>
            )}
            
              <FontAwesome5 name={breedActive ? "angle-up" : "angle-down"} size={16} className="absolute right-2" />
          </View>
        </Pressable>

        {breedActive && (
          <View className="mb-2">
            <BreedPicker mode="single" value={breed} onChange={setBreed} />
          </View>
        )}
      </View>

      <View className="bg-white px-4 pt-4 pb-2 mb-4 flex w-full rounded-xl">
        <Pressable
            onPress={() => setSizeActive(!sizeActive)}
            className="active:opacity-80"
        >
          <View className="flex-row items-center relative mb-4">
            <MaterialCommunityIcons name="ruler" size={16} color="brown" className="bg-yellow-100 px-2 py-2 rounded-xl" />
            <Text className="ml-2 font-semibold text-gray-800">Size</Text>
            {!!size && (
              <Text className="ml-2 text-sm text-blue-600 font-medium">{size}</Text>
            )}
            <FontAwesome5 name={sizeActive ? "angle-up" : "angle-down"} size={16} className="absolute right-2" />
          </View>
        </Pressable>

        {sizeActive && (
          <View className="flex-row gap-4 justify-center">
            {([
              { value: 'small', emoji: '🐶', label: 'Small', sub: '<10kg' },
              { value: 'medium', emoji: '🐕', label: 'Medium', sub: '10-25kg' },
              { value: 'large', emoji: '🦮', label: 'Large', sub: '25kg+' },
            ] as const).map(opt => {
              const active = size === opt.value
              return (
                <Pressable
                  key={opt.value}
                  className={`h-32 w-28 items-center justify-center border-2 rounded-xl active:opacity-80 ${active ? 'border-gray-400' : 'border-gray-200'}`}
                  onPress={() => setSize(opt.value)}
                >
                  <Text className="text-3xl mb-1">{opt.emoji}</Text>
                  <Text className={`font-semibold mb-1 ${active ? 'text-gray-800' : 'text-gray-500'}`}>{opt.label}</Text>
                  <Text className={`text-xs font-semibold ${active ? 'text-gray-600' : 'text-gray-400'}`}>{opt.sub}</Text>
                </Pressable>
              )
            })}
          </View>
        )}
      </View>

      <View className="bg-white px-4 pt-4 pb-2 mb-4 flex w-full rounded-xl">
        <Pressable
            onPress={() => setColorActive(!colorActive)}
            className="active:opacity-80"
        >
          <View className="flex-row items-center relative mb-4">
            <Ionicons name="color-palette-sharp" size={16} color="brown" className="bg-yellow-100 px-2 py-2 rounded-xl" />
            <Text className="ml-2 font-semibold text-gray-800">Color</Text>
            {colors.length > 0 && (
              <Text className="ml-2 text-sm text-blue-600 font-medium">
                {colors.map(c => COLOR_OPTIONS.find(o => o.value === c)?.label).join(', ')}
              </Text>
            )}
            <FontAwesome5 name={colorActive ? "angle-up" : "angle-down"} size={16} className="absolute right-2" />
          </View>
        </Pressable>

        {colorActive && (
          <View className="flex-row flex-wrap gap-2 mb-2">
            {COLOR_OPTIONS.map(opt => {
              const active = colors.includes(opt.value)
              return (
                <Pressable
                  key={opt.value}
                  onPress={() => toggleColor(opt.value)}
                  className={`flex-row items-center px-3.5 py-2.5 rounded-full border-2 active:opacity-80 ${
                    active ? 'bg-blue-600 border-blue-600' : 'bg-white border-gray-100'
                  }`}
                >
                  {opt.dot ? (
                    <View
                      className="w-3 h-3 rounded-full mr-1.5"
                      style={{
                        backgroundColor: opt.dot,
                        borderWidth: 'border' in opt ? 1 : 0,
                        borderColor: '#d1d5db',
                      }}
                    />
                  ) : (
                    <View className="w-3 h-3 rounded-full mr-1.5 overflow-hidden flex-row">
                      <View className="flex-1 bg-[#7c4a1e]" />
                      <View className="flex-1 bg-[#f0f0f0]" />
                      <View className="flex-1 bg-[#1a1a1a]" />
                    </View>
                  )}
                  <Text className={`text-sm font-semibold ${active ? 'text-white' : 'text-gray-700'}`}>
                    {opt.label}
                  </Text>
                </Pressable>
              )
            })}
          </View>
        )}
      </View>

      <View className="bg-white px-4 pt-4 pb-2 mb-4 flex w-full rounded-xl">
        <Pressable onPress={() => setGenderActive(!genderActive)} className="active:opacity-80">
          <View className="flex-row items-center relative mb-4">
            <Ionicons name="male-female" size={16} color="brown" className="bg-yellow-100 px-2 py-2 rounded-xl" />
            <Text className="ml-2 font-semibold text-gray-800">Gender</Text>
            {!!gender && (
              <Text className="ml-2 text-sm text-blue-600 font-medium capitalize">{gender}</Text>
            )}
            <FontAwesome5 name={genderActive ? "angle-up" : "angle-down"} size={16} className="absolute right-2" />
          </View>
        </Pressable>

        {genderActive && (
          <View className="flex-row gap-4 justify-center mb-2">
            {([
              { value: 'male', icon: 'male', label: 'Male', color: '#60a5fa' },
              { value: 'female', icon: 'female', label: 'Female', color: '#f472b6' },
              { value: 'unknown', icon: 'help-circle-outline', label: 'Unknown', color: '#9ca3af' },
            ] as const).map(opt => {
              const active = gender === opt.value
              return (
                <Pressable
                  key={opt.value}
                  className={`h-24 w-28 items-center justify-center border-2 rounded-xl active:opacity-80 ${active ? 'border-gray-400' : 'border-gray-200'}`}
                  onPress={() => setGender(opt.value)}
                >
                  <View className="mb-1">
                    <Ionicons name={opt.icon} size={32} color={active ? opt.color : '#9ca3af'} />
                  </View>
                  <Text className={`font-semibold ${active ? 'text-gray-800' : 'text-gray-500'}`}>{opt.label}</Text>
                </Pressable>
              )
            })}
          </View>
        )}
      </View>

      <View className="bg-white px-4 pt-4 pb-2 mb-4 flex w-full rounded-xl">
        <Pressable onPress={() => setExtrasActive(!extrasActive)} className="active:opacity-80">
          <View className="flex-row items-center relative mb-4">
            <Ionicons name="information-circle-outline" size={16} color="brown" className="bg-yellow-100 px-2 py-2 rounded-xl" />
            <Text className="ml-2 font-semibold text-gray-800">Extras</Text>
            <FontAwesome5 name={extrasActive ? "angle-up" : "angle-down"} size={16} className="absolute right-2" />
          </View>
        </Pressable>

        {extrasActive && (
          <View className="mb-2 gap-4">
            <View>
              <Text className="text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">Dog name</Text>
              <TextInput
                value={dogName}
                onChangeText={setDogName}
                placeholder="e.g. Buddy"
                placeholderTextColor="#9ca3af"
                className="border border-gray-200 rounded-xl px-3 py-2.5 text-gray-800"
              />
            </View>

            <View>
              <Text className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Age</Text>
              <View className="flex-row flex-wrap gap-2">
                {(['puppy', 'young', 'adult', 'senior'] as const).map(opt => (
                  <Pressable
                    key={opt}
                    onPress={() => setAge(age === opt ? '' : opt)}
                    className={`px-4 py-2 rounded-full border-2 active:opacity-80 ${age === opt ? 'bg-blue-600 border-blue-600' : 'bg-white border-gray-100'}`}
                  >
                    <Text className={`font-semibold capitalize text-sm ${age === opt ? 'text-white' : 'text-gray-600'}`}>{opt}</Text>
                  </Pressable>
                ))}
              </View>
            </View>

            <View>
              <Text className="text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">Special marks</Text>
              <TextInput
                value={specialMarks}
                onChangeText={setSpecialMarks}
                placeholder="e.g. scar on left ear, blue eyes"
                placeholderTextColor="#9ca3af"
                multiline
                numberOfLines={2}
                className="border border-gray-200 rounded-xl px-3 py-2.5 text-gray-800"
                style={{ textAlignVertical: 'top' }}
              />
            </View>

            {/* <View className="flex-row items-center justify-between">
              <View className="flex-row items-center gap-2">
                <MaterialCommunityIcons name="integrated-circuit-chip" size={18} color="#6366f1" />
                <Text className="font-semibold text-gray-800">Microchip</Text>
              </View>
              <Switch value={microchip} onValueChange={setMicrochip} />
            </View> */}

            <View>
              <View className="flex-row items-center justify-between">
                <View className="flex-row items-center gap-2">
                  <MaterialCommunityIcons name="dog-service" size={18} color="#6366f1" />
                  <Text className="font-semibold text-gray-800">Collar</Text>
                </View>
                <Switch value={hasCollar} onValueChange={setHasCollar} />
              </View>
              {hasCollar && (
                <TextInput
                  value={collarColor}
                  onChangeText={setCollarColor}
                  placeholder="Collar color / description"
                  placeholderTextColor="#9ca3af"
                  className="border border-gray-200 rounded-xl px-3 py-2.5 text-gray-800 mt-2"
                />
              )}
            </View>
          </View>
        )}
      </View>
    </ScrollView>
  )
}

export default DogDetailsStep
